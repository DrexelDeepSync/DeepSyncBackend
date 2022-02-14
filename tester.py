from FastAudioGenerator import FastAudioGenerator

if __name__ == "__main__":
    fastgen = FastAudioGenerator("test_resources/bd.wav", "test_resources/script.txt", "test_resources/fast_res.wav")
    fastgen.generateContent()