from src.generators.ContentGenerator import ContentGenerator
from libs.Wav2Lip.create_lip_sync import LipSyncer
import cv2

class AudioVisualGenerator(ContentGenerator):
    def __init__(self, audioPath: str, videoPath: str, outputPath: str):
        self._audioPath = audioPath
        self._videoPath = videoPath
        self._outputPath = outputPath

    def rescale_frame(self, frame_input, percent=.75):
        width = int(frame_input.shape[1] * percent)
        height = int(frame_input.shape[0] * percent)
        dim = (width, height)
        return cv2.resize(frame_input, dim, interpolation=cv2.INTER_AREA)

    def resize_video(self):
        vid = cv2.VideoCapture(self._videoPath)
        height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        percent = 720/height
        if height > 720:
            if vid.isOpened():
                _, frame = vid.read()
                rescaled_frame = self.rescale_frame(frame, percent)
                (h, w) = rescaled_frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter('Video_output.mp4',
                                        fourcc, 15.0,
                                        (w, h), True)
            
            while vid.isOpened():
                _, frame = vid.read()

                rescaled_frame = self.rescale_frame(frame, percent)

                # write the output frame to file
                writer.write(rescaled_frame)
            
            vid.release()
            writer.release()

    def generateContent(self) -> None:
        self.resize_video()
        ls = LipSyncer()
        ls.start_generation(self._videoPath, self._audioPath, self._outputPath)