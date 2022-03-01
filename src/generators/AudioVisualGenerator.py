from src.generators.ContentGenerator import ContentGenerator
from libs.Wav2Lip.create_lip_sync import LipSyncer

class AudioVisualGenerator(ContentGenerator):
    def __init__(self, audioPath: str, videoPath: str, outputPath: str):
        self._audioPath = audioPath
        self._videoPath = videoPath
        self._outputPath = outputPath

    def generateContent(self) -> None:
        ls = LipSyncer()
        ls.start_generation(self._videoPath, self._audioPath, self._outputPath)