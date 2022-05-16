from src.generators.ContentGenerator import ContentGenerator
from libs.Wav2Lip.create_lip_sync import LipSyncer
import cv2
import numpy as np

class AudioVisualGenerator(ContentGenerator):
    def __init__(self, audioPath: str, videoPath: str, outputPath: str):
        self._audioPath = audioPath
        self._videoPath = videoPath
        self._outputPath = outputPath

    def generateContent(self) -> None:
        vid = cv2.VideoCapture(self._videoPath)
        height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        resize = 1
        if height > 720:
            resize = int(np.ceil(height/720))
        ls = LipSyncer()
        ls.start_generation(self._videoPath, self._audioPath, self._outputPath, resize)