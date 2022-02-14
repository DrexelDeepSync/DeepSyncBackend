from email.mime import audio
from typing import Text
from src.ContentGenerator import ContentGenerator
from libs.RTVC.voice_synth import TextToSpeech

class FastAudioGenerator(ContentGenerator):
    def __init__(self, audioPath: str, scriptPath: str, outputPath: str):
        self._audioPath = audioPath
        self._scriptPath = scriptPath
        self._outputPath = outputPath

    def generateContent(self) -> None:
        tts = TextToSpeech()
        tts.convert_text_to_speech(self._scriptPath, self._audioPath, self._outputPath)