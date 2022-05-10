import pytest, os
from src.generators.SlowAudioGenerator import SlowAudioGenerator

class TestSlowAudioGenerator:
    scriptPath = "test_script.txt"
    outputPath = "test_resources/test_output.wav"

    def test_constructor(self):
        slowgen = SlowAudioGenerator(self.scriptPath, self.outputPath)
        assert slowgen._scriptPath == self.scriptPath
        assert slowgen._outputPath == self.outputPath

    def test_generation(self):
        slowgen = SlowAudioGenerator(self.scriptPath, self.outputPath)
        slowgen.generateContent()
        assert os.path.exists(self.outputPath)
        self.cleanup()

    def cleanup(self):
        os.remove(self.outputPath)
