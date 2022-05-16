from src.generators.ContentGenerator import ContentGenerator
from libs.Wav2Lip.create_lip_sync import LipSyncer
from moviepy.editor import *
import numpy as np

class AudioVisualGenerator(ContentGenerator):
    def __init__(self, audioPath: str, videoPath: str, outputPath: str):
        self._audioPath = audioPath
        self._videoPath = videoPath
        self._outputPath = outputPath

    def resize_video(self):
        clip = VideoFileClip(self._videoPath)
        if clip.h > 720:
            clip2 = clip.resize(720/clip.h)
            clip2.write_videofile(self._videoPath)

    def generateContent(self) -> None:
        self.resize_video()
        ls = LipSyncer()
        ls.start_generation(self._videoPath, self._audioPath, self._outputPath)