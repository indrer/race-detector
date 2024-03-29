import joblib
import numpy as np

class RaceDetector:
    def __init__(self):
        self._model = self.load_model()
        self._scaler = self.load_scaler()
    
    # returns predicted start and end of the race
    def get_race(self, data, rlen):
        # iterate voer windows and make predictions, save predictions in separate list
        # get possible races
        # get final race times
        cropped = self._clip_end(data)
        predictions = self._predict_windows(self._model, self._scaler, cropped['V(Acc)'].values, window_size=500, step_size=100)
        predictions.resize(len(cropped))
        possible_races = self._get_possible_races(predictions)
        joined = self._join_predictions(possible_races)
        pred = self._find_race(df=cropped, length=rlen, preds=joined)
        pred_start = pred[0]
        while cropped['V(Acc)'][pred_start] > 0.3:
            pred_start = pred_start - 1
        dist_start = cropped['Dist'][pred_start]
        dist_end = dist_start + rlen
        pred_end = cropped[pred_start:].loc[cropped['Dist'] >= dist_end].iloc[0]['Time'] * 100
        return int(pred_start), int(pred_end)

    def _predict_windows(self, clf, scaler, velocity, window_size=500, step_size=250):
        sh = (velocity.size - window_size + 1, window_size)
        st = velocity.strides * 2
        view = np.lib.stride_tricks.as_strided(velocity, strides = st, shape = sh)[0::step_size]
        res = [clf.predict(scaler.transform([x]))[0] for x in view]
        if step_size > 1:
            arr = np.zeros(len(velocity))
            i = 0
            for x in range(0, len(arr)-step_size, step_size):
                if i >= len(res):
                    break
                arr[x:(x+step_size-1)] = res[i]
                i = i + 1
            return arr
        return np.array(res)
    
    def _join_predictions(self, predictions):
        j = []
        curr = None
        i = 0
        while i < len(predictions):
            if curr is None:
                curr = predictions[i]
                if i ==(len(predictions)-1):
                    j.append(curr)
                    break
                i = i + 1
            else:
                if i ==(len(predictions)-1):
                    j.append(curr)
                    break
                nxt = predictions[i+1]
                diff = nxt[0] - curr[1]
                if diff < 800:
                    curr = (curr[0], nxt[1])
                    i = i + 1
                else:
                    j.append(curr)
                    curr = nxt
        crpj = []
        for i in j:
            if (i[1] - i[0]) > 3000:
                crpj.append(i)
        return crpj

    def _find_race(self, df, length, preds, thres=0.15):
        dists = []
        # Get distances of all predictions
        for p in preds:
            s = p[0]
            e = p[1]
            dist = df['Dist'][e] - df['Dist'][s]
            dists.append(dist)
        # find closest to the race distance
        closest = []
        print(length)
        perc = length * thres
        for idx, c in enumerate(dists):
            if abs(length - c) < perc:
                closest.append(idx)
        # if only one prediction matched length, we can add it, otherwise look
        # for predictions that start with a >0.5 value
        if len(closest) == 1:
            return preds[closest[0]]
        else:
            if len(closest) == 0:
                new_dists = np.array(dists)
                new_dists = np.argsort(new_dists)[:3]
                closest = new_dists.tolist()
            vel = df['vel']
            speedup = []
            for c in closest:
                s = e = preds[c][0]
                curr = vel[s]
                while curr>0.5:
                    s = s - 1
                    curr = vel[s]
                speedup.append(abs(vel[e]-vel[s]))
            idm = closest[speedup.index(min(speedup))]
            return preds[idm]   

    # df - dataframe
    # p - percentage to remove (in decimal, < 1), default 10%
    def _clip_end(self, df, p=0.1):
        n = len(df)
        m = round(n-(len(df) * p))
        return df[:m]

    def load_model(self):
        with open('ml/model/model.mod', 'rb') as f:
            return joblib.load(f)
    
    def load_scaler(self):
        with open('ml/model/scaler.mod', 'rb') as f:
            return joblib.load(f)
    
    def _get_possible_races(self, predictions):
        races = []
        occurences = np.where(predictions == 1)[0]
        i = 0
        start = occurences[i]
        end = 0
        for i in range(len(occurences)-1):
            if ((occurences[i] + 1) != occurences[i+1]) or ((i+1) == (len(occurences)-1)):
                end = occurences[i]
                # from the provided data, all races are at least 40 seconds
                #if (end-start) > 2000:
                races.append((start, end))
                start = occurences[i+1]
        return races
