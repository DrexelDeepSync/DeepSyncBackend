import enum
from app import create_app
from flask import request, jsonify
import os
import json

app = create_app()

@app.route("/fastaudio/generate", methods=["POST"])
def generateFastAudio():
    from src.generators.FastAudioGenerator import FastAudioGenerator

    rc = ReturnContent()

    req_json = request.get_json()

    if not "audioPath" in req_json or not os.path.isfile(req_json["audioPath"]):
        rc.code = RequestCode.BadAudio
        rc.message = "Missing audio file"
        return json.loads(rc.toJson())
    
    audio_path = req_json['audioPath']

    if not "scriptPath" in req_json or not os.path.isfile(req_json["scriptPath"]):
        rc.code = RequestCode.BadScript
        rc.message = "Missing script file"
        return json.loads(rc.toJson())
    
    script_path = req_json['scriptPath']

    if not "outputPath" in req_json:
        rc.code = RequestCode.BadOutput
        rc.message = "Missing output path"
        return json.loads(rc.toJson())

    output_path = req_json['outputPath']

    fast_gen = FastAudioGenerator(audio_path, script_path, output_path)
    fast_gen.generateContent()

    return json.loads(rc.toJson())

@app.route("/audiovisual/generate", methods=["POST"])
def generateAudioVisual():
    from src.generators.AudioVisualGenerator import AudioVisualGenerator

    req_json = request.get_json()

    rc = ReturnContent()

    if not "audioPath" in req_json or not os.path.isfile(req_json["audioPath"]):
        rc.code = RequestCode.BadAudio
        rc.message = "Missing audio file"
        return json.loads(rc.toJson())

    audio_path = req_json['audioPath']

    if not "videoPath" in req_json or not os.path.isfile(req_json["videoPath"]):
        rc.code = RequestCode.BadVideo
        rc.message = "Missing video file"
        return json.loads(rc.toJson())

    video_path = req_json['videoPath']

    if not "outputPath" in req_json:
        rc.code = RequestCode.BadOutput
        rc.message = "Missing output path"
        return json.loads(rc.toJson())

    output_path = req_json['outputPath']

    video_gen = AudioVisualGenerator(audio_path, video_path, output_path)
    video_gen.generateContent()

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

if __name__ == "__main__":
    app.run(port=5000, debug=True)