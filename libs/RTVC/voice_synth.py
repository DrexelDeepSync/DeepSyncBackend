from libs.RTVC.encoder.params_model import model_embedding_size as speaker_embedding_size
from libs.RTVC.utils.argutils import print_args
from libs.RTVC.utils.modelutils import check_model_paths
from libs.RTVC.synthesizer.inference import Synthesizer
from libs.RTVC.encoder import inference as encoder
from libs.RTVC.vocoder import inference as vocoder
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
import argparse
import torch
import sys
import os
from audioread.exceptions import NoBackendError

class TextToSpeech:

    def __init__(self):
        self.encModelPath=Path("libs/RTVC/encoder/saved_models/pretrained.pt".replace("\"", "").replace("\'", ""))
        self.synModelPath=Path("libs/RTVC/synthesizer/saved_models/pretrained/pretrained.pt".replace("\"", "").replace("\'", ""))
        self.vocModelPath=Path("libs/RTVC/vocoder/saved_models/pretrained/pretrained.pt".replace("\"", "").replace("\'", ""))
        self.cpu = False
        self.noSound = True
        self.noMp3Support = False

    def convert_text_to_speech(self, textToConvert, soundPath, nameOfFile, seed=None):
    
        if not self.noSound:
            import sounddevice as sd

        if self.cpu == True:
            # Hide GPUs from Pytorch to force CPU processing
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

        if not self.noMp3Support:
            try:
                librosa.load("libs/RTVC/samples/1320_00000.mp3")
            except NoBackendError:
                print("Librosa will be unable to open mp3 files if additional software is not installed.\n"
                    "Please install ffmpeg or add the '--no_mp3_support' option to proceed without support for mp3 files.")
                exit(-1)
            
        if torch.cuda.is_available():
            device_id = torch.cuda.current_device()
            gpu_properties = torch.cuda.get_device_properties(device_id)
            ## Print some environment information (for debugging purposes)
            print("Found %d GPUs available. Using GPU %d (%s) of compute capability %d.%d with "
                "%.1fGb total memory.\n" % 
                (torch.cuda.device_count(),
                device_id,
                gpu_properties.name,
                gpu_properties.major,
                gpu_properties.minor,
                gpu_properties.total_memory / 1e9))
        else:
            print("Using CPU for inference.\n")
        
        ## Remind the user to download pretrained models if needed
        check_model_paths(encoder_path=self.encModelPath,
                        synthesizer_path=self.synModelPath,
                        vocoder_path=self.vocModelPath)
        
        ## Load the models one by one.
        print("Preparing the encoder, the synthesizer and the vocoder...")
        encoder.load_model(self.encModelPath)
        synthesizer = Synthesizer(self.synModelPath)
        vocoder.load_model(self.vocModelPath)
        
        try:
            in_fpath = Path(soundPath.replace("\"", "").replace("\'", ""))

            if in_fpath.suffix.lower() == ".mp3" and self.noMp3Support:
                return -1
            ## Computing the embedding
            # First, we load the wav using the function that the speaker encoder provides. This is 
            # important: there is preprocessing that must be applied.
            
            # The following two methods are equivalent:
            # - Directly load from the filepath:
            preprocessed_wav = encoder.preprocess_wav(in_fpath)
            # - If the wav is already loaded:
            #original_wav, sampling_rate = librosa.load(str(in_fpath))
            #preprocessed_wav = encoder.preprocess_wav(original_wav, sampling_rate)
            print("Loaded file succesfully")
            
            # Then we derive the embedding. There are many functions and parameters that the 
            # speaker encoder interfaces. These are mostly for in-depth research. You will typically
            # only use this function (with its default parameters):
            embed = encoder.embed_utterance(preprocessed_wav)
            print("Created the embedding")
            
            # If seed is specified, reset torch seed and force synthesizer reload
            if seed is not None:
                torch.manual_seed(seed)
                synthesizer = Synthesizer(self.synModelPath)

            # The synthesizer works in batch, so you need to put your data in a list or numpy array
            texts = [textToConvert]
            embeds = [embed]
            # If you know what the attention layer alignments are, you can retrieve them here by
            # passing return_alignments=True
            specs = synthesizer.synthesize_spectrograms(texts, embeds)
            spec = specs[0]
            print("Created the mel spectrogram")
            
            
            ## Generating the waveform
            print("Synthesizing the waveform:")

            # If seed is specified, reset torch seed and reload vocoder
            if seed is not None:
                torch.manual_seed(seed)
                vocoder.load_model(self.vocModelPath)

            print(torch.from_numpy(spec).unsqueeze(0).shape)

            # Synthesizing the waveform is fairly straightforward. Remember that the longer the
            # spectrogram, the more time-efficient the vocoder.
            generated_wav = vocoder.infer_waveform(spec)
            
            
            ## Post-generation
            # There's a bug with sounddevice that makes the audio cut one second earlier, so we
            # pad it.
            #generated_wav = np.pad(generated_wav, (0, synthesizer.sample_rate), mode="constant")

            # Trim excess silences to compensate for gaps in spectrograms (issue #53)
            generated_wav = encoder.preprocess_wav(generated_wav)
            
            # Play the audio (non-blocking)
            if not self.noSound:
                try:
                    sd.stop()
                    sd.play(generated_wav, synthesizer.sample_rate)
                except sd.PortAudioError as e:
                    print("\nCaught exception: %s" % repr(e))
                    print("Continuing without audio playback. Suppress this message with the \"--no_sound\" flag.\n")
                except:
                    raise
                
            # Save it on the disk
            filename = nameOfFile
            print(generated_wav.dtype)
            sf.write(filename, generated_wav.astype(np.float32), synthesizer.sample_rate)
            print("\nSaved output as %s\n\n" % filename)
            
            
        except Exception as e:
            print("Caught exception: %s" % repr(e))
            return -1

        return 1

