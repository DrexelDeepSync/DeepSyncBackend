import pytest, os
from src.generators.AudioVisualGenerator import AudioVisualGenerator

class TestAudioVisualGenerator:
    audioPath = "test_resources/test_audio.wav"
    videoPath = "test_resources/test_image.jpg"
    outputPath = "test_resources/test_output.mp4"

    def test_constructor(self):
        audvisgen = AudioVisualGenerator(self.audioPath, self.videoPath, self.outputPath)
        assert audvisgen._audioPath == self.audioPath
        assert audvisgen._videoPath == self.videoPath
        assert audvisgen._outputPath == self.outputPath

    def test_generation(self):
        audvisgen = AudioVisualGenerator(self.audioPath, self.videoPath, self.outputPath)
        audvisgen.generateContent()
        assert os.path.exists(self.outputPath)
        self.cleanup()

    def cleanup(self):
        os.remove(self.outputPath)
