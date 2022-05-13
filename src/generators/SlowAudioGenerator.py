from src.generators.ContentGenerator import ContentGenerator
import glob
import os
import numpy as np
import kaldiio
import torch
import torchaudio
from espnet2.bin.tts_inference import Text2Speech
from espnet2.utils.types import str_or_none

# vocoder_tag = "parallel_wavegan/vctk_parallel_wavegan.v1.long"
# vocoder_tag = "parallel_wavegan/vctk_multi_band_melgan.v2"
# vocoder_tag = "parallel_wavegan/vctk_style_melgan.v1"
vocoder_tag = "parallel_wavegan/vctk_hifigan.v1"
# vocoder_tag = "parallel_wavegan/libritts_parallel_wavegan.v1.long"
# vocoder_tag = "parallel_wavegan/libritts_multi_band_melgan.v2"
# vocoder_tag = "parallel_wavegan/libritts_hifigan.v1"
# vocoder_tag = "parallel_wavegan/libritts_style_melgan.v1"
# vocoder_tag = None

ESPNET_ROOT = "/home/ubuntu/espnet/egs2/vctk/tts1"

text2speech = Text2Speech.from_pretrained(
    model_file=(f"{ESPNET_ROOT}/exp/tts_train_xvector_tacotron2_raw_phn_tacotron_g2p_en_no_space/train.loss.ave_5best.pth"),
    train_config=(f"{ESPNET_ROOT}/exp/tts_train_xvector_tacotron2_raw_phn_tacotron_g2p_en_no_space/config.yaml"),
    vocoder_tag=vocoder_tag,
    device="cuda",
    # Only for Tacotron 2 & Transformer
    threshold=0.5,
    # Only for Tacotron 2
    minlenratio=0.0,
    maxlenratio=10.0,
    use_att_constraint=True,
    backward_window=1,
    forward_window=3,
    # Only for FastSpeech & FastSpeech2 & VITS
    speed_control_alpha=1.0,
    # Only for VITS
    noise_scale=0.333,
    noise_scale_dur=0.333,
)
spembs = None
xvector_ark = [p for p in glob.glob(f"{ESPNET_ROOT}/dump/**/spk_xvector.ark", recursive=True) if "tr" in p][0]
xvectors = {k: v for k, v in kaldiio.load_ark(xvector_ark)}

def generate(msg, spk):
    spembs = xvectors[spk]
    with torch.no_grad():
        wav = text2speech(msg, spembs=spembs)["wav"]
    try:
        os.remove("/tmp/generated.wav")
    except FileNotFoundError:
        pass
    torchaudio.save("/tmp/generated.wav", wav.cpu(), text2speech.fs)
    seg = pydub.AudioSegment.from_file("/tmp/generated.wav", format="wav")
    os.remove("/tmp/generated.wav")
    return seg


class SlowAudioGenerator(ContentGenerator):
    def __init__(self, scriptPath: str, outputPath: str):
        self._scriptPath = scriptPath
        self._outputPath = outputPath
        self._speaker = 'p291'

    def generateContent(self) -> None:
        msg = open(os.path.join("resources", self._scriptPath), "r").read()

        all_sentences = []

        for sentence in msg.split("."):
            new_sentence = sentence.strip()
            if len(new_sentence) == 0:
                continue
            new_sentence += "."

            phrases = re.split("[,;]", new_sentence)

            all_sentences.append([phrase.strip() for phrase in phrases])

        final = pydub.AudioSegment.empty()

        for sentence in all_sentences:
            print(sentence)
            start_time = time.time()
            for phrase in sentence:
                gen_audio = generate.generate(phrase, self._speaker)
                final += gen_audio
                if phrase[-1] == ".":
                    final += pydub.AudioSegment.silent(duration=400, frame_rate=24000)
                else:
                    final += pydub.AudioSegment.silent(duration=200, frame_rate=24000)
            end_time = time.time()
            print(end_time - start_time)

        final.export(self._outputPath, format="wav")
