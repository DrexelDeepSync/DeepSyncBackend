import enum

from sympy import re
from app import create_app
from flask import request, send_file
from werkzeug.utils import secure_filename
import os
import json

app = create_app()

def getFileNum():
    return len([name for name in os.listdir('resources')])

@app.route("/resources/<path>")
def serve_video(path):
    return send_file(os.path.join("resources", path), mimetype = 'video/mp4')


@app.route("/uploadfile", methods=["POST"])
def uploadFile():
    rc = ReturnContent()

    print(request.data)
    print(request.form)
    print(request.files)
    req_data = request.form

    if not "fileName" in req_data:
        rc.code = RequestCode.BadFileName
        rc.message = "Missing file name"
        return json.loads(rc.toJson())
    
    numFiles = getFileNum()

    file_name = req_data['fileName'] + "_" + str(numFiles) + req_data['fileType']

    f = request.files['file']
    f.save(os.path.join("resources", secure_filename(file_name)))

    rc.message = file_name

    return json.loads(rc.toJson())

""" 
@app.route("/fastaudio/generate", methods=["POST"])
def generateFastAudio():
    from src.generators.FastAudioGenerator import FastAudioGenerator

    rc = ReturnContent()

    req_json = request.get_json()

    if not "audioPath" in req_json or not os.path.isfile(os.path.join("resources", req_json["audioPath"])):
        rc.code = RequestCode.BadAudio
        rc.message = "Missing audio file"
        return json.loads(rc.toJson())
    
    audio_path = req_json['audioPath']

    if not "scriptPath" in req_json or not os.path.isfile(os.path.join("resources", req_json["scriptPath"])):
        rc.code = RequestCode.BadScript
        rc.message = "Missing script file"
        return json.loads(rc.toJson())
    
    script_path = req_json['scriptPath']

    #if not "outputPath" in req_json:
    #    rc.code = RequestCode.BadOutput
    #    rc.message = "Missing output path"
    #    return json.loads(rc.toJson())

    outputFile = "audio" + str(getFileNum()) + ".wav"

    audio_path = os.path.join("resources", audio_path)
    script_path = os.path.join("resources", script_path)
    output_path = os.path.join("resources", outputFile)

    fast_gen = FastAudioGenerator(audio_path, script_path, output_path)
    fast_gen.generateContent()

    rc.message = outputFile

    return json.loads(rc.toJson())
"""

@app.route("/slowaudio/generate", methods=["POST"])
def generateSlowAudio():
    from src.generators.SlowAudioGenerator import SlowAudioGenerator

    rc = ReturnContent()

    req_json = request.get_json()

    if not "scriptPath" in req_json or not os.path.isfile(os.path.join("resources", req_json["scriptPath"])):
        rc.code = RequestCode.BadScript
        rc.message = "Missing script file"
        return json.loads(rc.toJson())

    script_path = req_json['scriptPath']

    #if not "outputPath" in req_json:
    #    rc.code = RequestCode.BadOutput
    #    rc.message = "Missing output path"
    #    return json.loads(rc.toJson())

    outputFile = "audio" + str(getFileNum()) + ".wav"

    output_path = os.path.join("resources", outputFile)

    slow_gen = SlowAudioGenerator(script_path, output_path)
    slow_gen.generateContent()

    rc.message = outputFile

    return json.loads(rc.toJson())

@app.route("/audiovisual/generate", methods=["POST"])
def generateAudioVisual():
    from src.generators.AudioVisualGenerator import AudioVisualGenerator

    req_json = request.get_json()
    print(req_json)

    rc = ReturnContent()

    if not "audioPath" in req_json or not os.path.isfile(os.path.join("resources", req_json["audioPath"])):
        rc.code = RequestCode.BadAudio
        rc.message = "Missing audio file"
        return json.loads(rc.toJson())

    audio_path = os.path.join("resources", req_json["audioPath"])

    if not "videoPath" in req_json or not os.path.isfile(os.path.join("resources", req_json["videoPath"])):
        rc.code = RequestCode.BadVideo
        rc.message = "Missing video file"
        return json.loads(rc.toJson())

    video_path = os.path.join("resources", req_json["videoPath"])

    #if not "outputPath" in req_json:
    #    rc.code = RequestCode.BadOutput
    #    rc.message = "Missing output path"
    #    return json.loads(rc.toJson())

    outputFile = "fakedvideo_" + str(getFileNum()) + ".mp4"

    output_path = os.path.join("resources", outputFile)

    video_gen = AudioVisualGenerator(audio_path, video_path, output_path)
    video_gen.generateContent()

    rc.message = output_path

    return json.loads(rc.toJson())

class ReturnContent():
    def __init__(self):
        self.code = RequestCode.Success
        self.message = "Success"

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class RequestCode(str, enum.Enum):
    Success: str = "200"
    BadAudio: str = "401"
    BadVideo: str = "402"
    BadScript: str = "403"
    BadOutput: str = "405"
    BadFileName: str = "406"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
