from src.generators.ContentGenerator import ContentGenerator
from libs.RTVC.voice_synth import TextToSpeech

class FastAudioGenerator(ContentGenerator):
    def __init__(self, audioPath: str, scriptPath: str, outputPath: str):
        self._audioPath = audioPath
        self._scriptPath = scriptPath
        self._outputPath = outputPath

    def generateContent(self) -> None:
        tts = TextToSpeech()
        msg = open(self._scriptPath, "r").read()
        tts.convert_text_to_speech(msg, self._audioPath, self._outputPath)
