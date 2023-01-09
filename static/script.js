window.addEventListener('DOMContentLoaded', init);

var file;
function init() {
    if (document.querySelector('.is-js') !== null) {
        window.addEventListener('dragenter', handleDragEnter);
        window.addEventListener('dragleave', handleDragLeave);
        window.addEventListener('dragover', handleDragOver);
        window.addEventListener('drop', handleDrop);
        document.querySelector('#uploadButton').addEventListener('click', handleUploadButton);
        document.querySelector('#detectButton').addEventListener('click', handleDetectButton);
        document.querySelector('.is-js').style.display = "flex";
        window.addEventListener('keydown', handleEnterKey);
        document.querySelector('#rlen').addEventListener('keypress', handleEnterKey);
    }
    initCanvas();
}

function prevent(event) {
    event.stopPropagation();
    event.preventDefault();
}

function handleDragEnter(event) {
    prevent(event);
    document.querySelector("#main").classList.add('active');
}

function handleDragLeave(event) {
    prevent(event);
    document.querySelector("#main").classList.remove('active');
}

function handleDragOver(event) {
    prevent(event);
    document.querySelector("#main").classList.add('active');
}

function handleDrop(event) {
    prevent(event);
    let dataTransfer = event.dataTransfer
    let dataTransferFile = dataTransfer.files[0];
    handleFile(dataTransferFile)
}

function handleFile(dataTransferFile) {
    console.log(dataTransferFile);
    file = dataTransferFile;
    document.querySelector("#fileDisplay").classList.remove('hidden');
    document.querySelector('#filename').textContent = file.name;
    
}

function handleEnterKey(event) {
    if (event.key === "Enter") {
        prevent(event);
        document.querySelector("#detectButton").click();
    }
}

function handleUploadButton(event) {
    prevent(event);
    let input = document.createElement('input');
    input.type = 'file';
    input.name = 'data-file';
    input.accept = '.csv';
    input.addEventListener('change', event => {
        file = input.files[0]; 
        document.querySelector("#fileDisplay").classList.remove('hidden');
        document.querySelector('#filename').textContent = file.name;
    });
    input.click();
}

function handleDetectButton(event) {
    prevent(event);
    document.querySelector(".spinner-container").style.display = "flex";
    document.querySelector("#detectButton svg").style.display = "none";
    let formData = new FormData();
    formData.append('data-file', file);
    formData.append('rlen', document.querySelector('#rlen').value);

    fetch("/", {
        body: formData,
        method: "post"
    }).then(resp => resp.text()).then(data => {
        document.open();
        document.write(data);
        document.close();
        // document.addEventListener('DOMContentLoaded', init);
    });
}

function initCanvas() {
    var canvas = document.getElementById("canvas");
    var context = canvas.getContext("2d");

    function start() {

    context.clearRect(0, 0, canvas.width, canvas.height);
    drawCurves(context, step);

    step += 1;
    window.requestAnimationFrame(start);
    }

    var step = -1;

    function drawCurves(ctx, step) {
        var width = ctx.canvas.width;
        ctx.beginPath();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "rgb(51,51,51)";

        var x = 0;
        var y = 0;
        var amplitude = 8;
        var frequency = width / (2 * Math.PI);
        ctx.save();
        ctx.translate(0, -amplitude * Math.sin(step / frequency));
        while (x < width) {
            y = width / 32 + amplitude * Math.sin((x + step) / frequency);
            ctx.lineTo(x, y);
            x++;
        }
        ctx.stroke();
        ctx.restore();
    }

    start();
}
