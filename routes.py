from app import create_app
from flask import request, jsonify

app = create_app()

@app.route("/fastaudio/generate", methods=["POST"])
def generateFastAudio():
    from src.generators.FastAudioGenerator import FastAudioGenerator

    req_json = request.get_json()

    audio_path = req_json['audioPath']
    script_path = req_json['scriptPath']
    output_path = req_json['outputPath']

    fast_gen = FastAudioGenerator(audio_path, script_path, output_path)
    fast_gen.generateContent()

    return jsonify("Success")

if __name__ == "__main__":
    app.run(port=5000, debug=True)