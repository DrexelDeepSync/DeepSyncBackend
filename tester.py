from src.generators.FastAudioGenerator import FastAudioGenerator
from src.generators.AudioVisualGenerator import AudioVisualGenerator

if __name__ == "__main__":
    fastgen = FastAudioGenerator("resources/bd.wav", "resources/script.txt", "resources/fast_res.wav")
    fastgen.generateContent()
    audioVisualGen = AudioVisualGenerator("resources/audio.wav", "resources/video.mp4", "resources/result.mp4")
    audioVisualGen.generateContent()
