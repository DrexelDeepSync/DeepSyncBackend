from os import listdir, path
import numpy as np
import scipy
import cv2
import os
import sys
import argparse
import libs.Wav2Lip.audio as audio
import json
import subprocess
import random
import string
from tqdm import tqdm
from glob import glob
import torch
import libs.Wav2Lip.face_detection as face_detection
from libs.Wav2Lip.models import Wav2Lip
import platform

class LipSyncer:

    def __init__(self):
        self.chkPtPath = "libs/Wav2Lip/checkpoints/wav2lip.pth"
        self.static = False
        self.fps = 25.0
        # Padding (top, bottom, left, right). Please adjust to include chin at least
        self.pads = [0, 10, 0, 0]
        self.faceDetBatchSize = 8
        self.wav2LipBatchSize = 8
        # Reduce the resolution by this factor. Sometimes, best results are obtained at 480p or 720p
        self.resizeFactor = 1
        # Crop video to a smaller region (top, bottom, left, right). Applied after resize_factor and rotate arg. '
        # 'Useful if multiple face present. -1 implies the value will be auto-inferred based on height, width
        self.crop = [0, -1, 0, -1]
        # Specify a constant bounding box for the face. Use only as a last resort if the face is not detected.'
        # 'Also, might work only if the face is not moving around much. Syntax: (top, bottom, left, right).
        self.box = [-1, -1, -1, -1]
        # Sometimes videos taken from a phone can be flipped 90deg. If true, will flip video right by 90deg.'
        # 'Use if you get a flipped result, despite feeding a normal looking video
        self.rotate = False
        # Prevent smoothing face detections over a short temporal window
        self.noSmooth = False
        self.imgSize = 96
        self.device = 'cpu'
        self.mel_step_size = 16

    def start_generation(self, facePath, audioPath, outputPath, resize=1):
        self.resizeFactor = resize
        full_frames = []

        if os.path.isfile(facePath) and facePath.split('.')[1] in ['jpg', 'png', 'jpeg']:
            self.static = True

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print('Using {} for inference.'.format(self.device))

        if not os.path.isfile(facePath):
            raise ValueError(
                'facePath argument must be a valid path to video/image file')
        elif facePath.split('.')[1] in ['jpg', 'png', 'jpeg']:
            full_frames = [cv2.imread(facePath)]
        else:
            video_stream = cv2.VideoCapture(facePath)
            self.fps = video_stream.get(cv2.CAP_PROP_FPS)

            print('Reading video frames...')

            full_frames = []
            while 1:
                still_reading, frame = video_stream.read()
                if not still_reading:
                    video_stream.release()
                    break
                if self.resizeFactor > 1:
                    frame = cv2.resize(
                        frame, (frame.shape[1]//self.resizeFactor, frame.shape[0]//self.resizeFactor))

                if self.rotate:
                    frame = cv2.rotate(frame, cv2.cv2.ROTATE_90_CLOCKWISE)

                y1, y2, x1, x2 = self.crop
                if x2 == -1:
                    x2 = frame.shape[1]
                if y2 == -1:
                    y2 = frame.shape[0]

                frame = frame[y1:y2, x1:x2]

                full_frames.append(frame)

        print("Number of frames available for inference: "+str(len(full_frames)))

        if not audioPath.endswith('.wav'):
            print('Extracting raw audio...')
            command = 'ffmpeg -y -i {} -strict -2 {}'.format(
                audioPath, 'temp/temp.wav')

            subprocess.call(command, shell=True)
            audioPath = 'temp/temp.wav'

        wav = audio.load_wav(audioPath, 16000)
        mel = audio.melspectrogram(wav)
        print(mel.shape)

        if np.isnan(mel.reshape(-1)).sum() > 0:
            raise ValueError(
                'Mel contains nan! Using a TTS voice? Add a small epsilon noise to the wav file and try again')

        mel_chunks = []
        mel_idx_multiplier = 80./self.fps
        i = 0
        while 1:
            start_idx = int(i * mel_idx_multiplier)
            if start_idx + self.mel_step_size > len(mel[0]):
                mel_chunks.append(mel[:, len(mel[0]) - self.mel_step_size:])
                break
            mel_chunks.append(mel[:, start_idx: start_idx + self.mel_step_size])
            i += 1

        print("Length of mel chunks: {}".format(len(mel_chunks)))

        full_frames = full_frames[:len(mel_chunks)]

        batch_size = self.wav2LipBatchSize
        gen = self.datagen(full_frames.copy(), mel_chunks)

        for i, (img_batch, mel_batch, frames, coords) in enumerate(tqdm(gen,
                                                                        total=int(np.ceil(float(len(mel_chunks))/batch_size)))):
            if i == 0:
                model = self.load_model(self.chkPtPath)
                print("Model loaded")

                frame_h, frame_w = full_frames[0].shape[:-1]
                out = cv2.VideoWriter('libs/Wav2Lip/temp/result.avi',
                                      cv2.VideoWriter_fourcc(*'DIVX'), self.fps, (frame_w, frame_h))

            img_batch = torch.FloatTensor(
                np.transpose(img_batch, (0, 3, 1, 2))).to(self.device)
            mel_batch = torch.FloatTensor(
                np.transpose(mel_batch, (0, 3, 1, 2))).to(self.device)

            with torch.no_grad():
                pred = model(mel_batch, img_batch)

            pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.

            for p, f, c in zip(pred, frames, coords):
                y1, y2, x1, x2 = c
                p = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))

                f[y1:y2, x1:x2] = p
                out.write(f)

        out.release()

        command = 'ffmpeg -y -i {} -i {} -strict -2 -q:v 1 {}'.format(
            audioPath, 'libs/Wav2Lip/temp/result.avi', outputPath)
        subprocess.call(command, shell=platform.system() != 'Windows')

    def get_smoothened_boxes(self, boxes, T):
        for i in range(len(boxes)):
            if i + T > len(boxes):
                window = boxes[len(boxes) - T:]
            else:
                window = boxes[i: i + T]
            boxes[i] = np.mean(window, axis=0)
        return boxes

    def face_detect(self, images):
        detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D,
                                                flip_input=False, device=self.device)

        batch_size = self.faceDetBatchSize

        while 1:
            predictions = []
            try:
                for i in tqdm(range(0, len(images), batch_size)):
                    predictions.extend(detector.get_detections_for_batch(
                        np.array(images[i:i + batch_size])))
            except RuntimeError:
                if batch_size == 1:
                    raise RuntimeError(
                        'Image too big to run face detection on GPU. Please use the --resize_factor argument')
                batch_size //= 2
                print('Recovering from OOM error; New batch size: {}'.format(batch_size))
                continue
            break

        results = []
        pady1, pady2, padx1, padx2 = self.pads
        for rect, image in zip(predictions, images):
            if rect is None:
                # check this frame where the face was not detected.
                cv2.imwrite('temp/faulty_frame.jpg', image)
                raise ValueError(
                    'Face not detected! Ensure the video contains a face in all the frames.')

            y1 = max(0, rect[1] - pady1)
            y2 = min(image.shape[0], rect[3] + pady2)
            x1 = max(0, rect[0] - padx1)
            x2 = min(image.shape[1], rect[2] + padx2)

            results.append([x1, y1, x2, y2])

        boxes = np.array(results)
        if not self.noSmooth:
            boxes = self.get_smoothened_boxes(boxes, T=5)
        results = [[image[y1: y2, x1:x2], (y1, y2, x1, x2)]
                   for image, (x1, y1, x2, y2) in zip(images, boxes)]

        del detector
        return results

    def datagen(self, frames, mels):
        img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

        if self.box[0] == -1:
            if not self.static:
                # BGR2RGB for CNN face detection
                face_det_results = self.face_detect(frames)
            else:
                face_det_results = self.face_detect([frames[0]])
        else:
            print('Using the specified bounding box instead of face detection...')
            y1, y2, x1, x2 = self.box
            face_det_results = [
                [f[y1: y2, x1:x2], (y1, y2, x1, x2)] for f in frames]

        for i, m in enumerate(mels):
            idx = 0 if self.static else i % len(frames)
            frame_to_save = frames[idx].copy()
            face, coords = face_det_results[idx].copy()

            face = cv2.resize(face, (self.imgSize, self.imgSize))

            img_batch.append(face)
            mel_batch.append(m)
            frame_batch.append(frame_to_save)
            coords_batch.append(coords)

            if len(img_batch) >= self.wav2LipBatchSize:
                img_batch, mel_batch = np.asarray(
                    img_batch), np.asarray(mel_batch)

                img_masked = img_batch.copy()
                img_masked[:, self.imgSize//2:] = 0

                img_batch = np.concatenate(
                    (img_masked, img_batch), axis=3) / 255.
                mel_batch = np.reshape(
                    mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

                yield img_batch, mel_batch, frame_batch, coords_batch
                img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

        if len(img_batch) > 0:
            img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

            img_masked = img_batch.copy()
            img_masked[:, self.imgSize//2:] = 0

            img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.
            mel_batch = np.reshape(
                mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

            yield img_batch, mel_batch, frame_batch, coords_batch

    def _load(self, checkpoint_path):
        if self.device == 'cuda':
            checkpoint = torch.load(checkpoint_path)
        else:
            checkpoint = torch.load(checkpoint_path,
                                    map_location=lambda storage, loc: storage)
        return checkpoint

    def load_model(self, path):
        model = Wav2Lip()
        print("Load checkpoint from: {}".format(path))
        checkpoint = self._load(path)
        s = checkpoint["state_dict"]
        new_s = {}
        for k, v in s.items():
            new_s[k.replace('module.', '')] = v
        model.load_state_dict(new_s)

        model = model.to(self.device)
        return model.eval()
