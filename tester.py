from src.generators.FastAudioGenerator import FastAudioGenerator
from src.generators.AudioVisualGenerator import AudioVisualGenerator

if __name__ == "__main__":
    #fastgen = FastAudioGenerator("test_resources/bd.wav", "test_resources/script.txt", "test_resources/fast_res.wav")
    #fastgen.generateContent()
    audioVisualGen = AudioVisualGenerator("test_resources/audio.wav", "test_resources/video.mp4", "test_resources/result.mp4")
    audioVisualGen.generateContent()