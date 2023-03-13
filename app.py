from flask import Flask, render_template, make_response, request, Response
import pandas as pd
from ml.detector.estimator import RaceDetector
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
import base64
import traceback

matplotlib.use('agg')

FILE_EXTENSIONS = ['csv']

app = Flask(__name__)
detector = RaceDetector()
df = None
original = None
start = 0
stop = 0
rlen = 0
filename = ''

def check_valid_file(name):
    return ('.' in name) and (name.split('.')[1].lower() in FILE_EXTENSIONS)

# Method to find the position of nth occurence of a char in a string
# str - string
# c - character/substring
# n - which occurence
def find_nth(str, c, n):
    start = str.find(c)
    while start >= 0 and n > 1:
        start = str.find(c, start+len(c))
        n -= 1
    return start

def read_file(fl):
    global df
    SEP = ','
    farr =  fl.read().decode('utf-8').split('\n')
    # Get header
    header = ['Time', 'Sats', 'Vel', 'V(Acc)', 'Dist', 'StRate', 'Acc(1)', 'Acc(2)', 'Acc(3)', 'Ac3Dif', 'Yaw', 'Pitch', 'Roll', 'GyroRaw1', 'GyroRaw2', 'GyroRaw3', 'Gyr0[degrees/s]', 'Gyr1[degrees/s]', 'Gyr2[degrees/s]', 'Mag1', 'Mag2', 'Mag3', 'Stk']
    #header = ['Time', 'Sats', 'Vel', 'V(Acc)', 'Dist']
    # Just sensor data without Logan information
    stripped_file = farr[4:-1]
    sep_num = len(header)
    new_data = list()
    new_data.append(header)
    # Save just the time and velocity data
    for line in stripped_file:
        end = find_nth(line, SEP, sep_num)
        new_data.append(line[0:end].split(','))
    df = pd.DataFrame(new_data[1:], columns=new_data[0])
    df_original = df.copy(deep=True)
    df = df.drop(['Sats', 'Vel', 'StRate', 'Acc(1)', 'Acc(2)', 'Acc(3)', 'Ac3Dif', 'Yaw', 'Pitch', 'Roll', 'GyroRaw1', 'GyroRaw2', 'GyroRaw3', 'Gyr0[degrees/s]', 'Gyr1[degrees/s]', 'Gyr2[degrees/s]', 'Mag1', 'Mag2', 'Mag3', 'Stk'], axis=1)
    df = df.astype(float)
    return df, df_original

def generate_plot(df, start, end):
    plt.rcParams["figure.figsize"] = (15,4)
    plt.figure(facecolor='#fafafa')
    plt.plot(df['Time'], df['V(Acc)'])
    plt.plot(df['Time'][start:end], df['V(Acc)'][start:end], color='orange')  
    plt.plot(df['Time'][start], df['V(Acc)'][start], marker='o', color='red')
    plt.plot(df['Time'][end], df['V(Acc)'][end], marker='o', color='red')
    plt.xlabel('Time')
    plt.ylabel('Velocity')
    plt.tight_layout()
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    url = base64.b64encode(img.getvalue()).decode('utf8')
    return url

def predict_race(f, name, racelen):
    global start, stop, df, original, filename, rlen
    df, original = read_file(f)
    filename = name
    try:
        start, stop = detector.get_race(df, racelen)
        rlen = racelen
    except Exception as e:
        traceback.print_exc()
        return render_template('index.html', msg='Make sure you are using Logan generated .csv file.')
    result = {'start': start,
                'end': stop,
                'len': rlen,
                'name': name.replace('.csv', ''),
                'image': generate_plot(df, start, stop)}
    return render_template('results.html', info=result)



@app.route('/', methods=['GET', 'POST'])
def index():
    global df, start, stop, rlen, filename
    if request.method == 'GET':
        df = None
        start = 0
        stop = 0
        rlen = 0
        filename = ''
        return render_template('index.html')
    elif request.method == 'POST':
        # Check if lenght is correct
        l = request.form['rlen']
        if not l.isnumeric():
            return render_template('index.html', msg='Make sure race length is a number!')
        # Check if file is correct
        f = request.files['data-file']
        if not f:
            return render_template('index.html', msg='No file selected.')
        if not check_valid_file(f.filename):
            return render_template('index.html', msg='Only .csv files allowed.')
        return predict_race(f, f.filename, int(l))

# example
#type=LOGAN
#version=V48.36
#race=201.55,1000.00,169244,189398,"K2 1000m heat",0,
#raceSplits=
@app.route('/get_vid')
def getvid():
    global df, start, stop, rlen, filename
    time = df['Time'][stop] - df['Time'][start]
    line1 = 'type=LOGAN\n'
    line2 = 'version=V48.36\n'
    line3 = 'race=' + str(round(time,2)) + ',' + str(round(rlen, 2)) + ',' + str(start) + ',' + str(stop)
    f = [line1, line2, line3]
    generator = (cell for row in f for cell in row)
    fn = filename.replace('.csv', '.vid')

    return Response(generator,
                       mimetype="text/plain",
                       headers={"Content-Disposition":
                                    "attachment;filename=" + fn})


@app.route('/get_csv')
def getcsv():
    global original, start, stop, filename
    fn = filename.replace('.csv', '')
    race = original.iloc[start:stop]
    resp = make_response(race.to_csv(index=False))
    resp.headers['Content-Disposition'] = 'attachment; filename='+fn+'-race.csv'
    resp.headers['Content-Type'] = 'text/csv'
    return resp



@app.route('/results', methods=['GET'])
def results():
    return render_template('results.html')


if __name__ == "__main__":
    app.run('0.0.0.0', '8080')