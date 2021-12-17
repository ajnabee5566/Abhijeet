import face_recognition
from torch.utils.data import Dataset
from facenet_pytorch.models.mtcnn import MTCNN
from PIL import Image
import cv2
from typing import List
from collections import OrderedDict
from abc import ABC, abstractmethod
import os
import numpy as np
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"


cv2.ocl.setUseOpenCL(False)
cv2.setNumThreads(0)


class VideoFaceDetector(ABC):

    def __init__(self, **kwargs) -> None:
        super().__init__()

    @property
    @abstractmethod
    def _batch_size(self) -> int:
        pass

    @abstractmethod
    def _detect_faces(self, frames) -> List:
        pass


class FacenetDetector(VideoFaceDetector):

    def __init__(self, detector="MTCNN", device="cuda:0") -> None:
        super().__init__()
        self.detector_type = detector
        if detector == "MTCNN":
            self.detector = MTCNN(margin=0, thresholds=[
                                  0.85, 0.95, 0.95], device=device)
        if detector == "face_recognition":
            self.detector = face_recognition

    def _detect_faces(self, frames) -> List:
        batch_boxes = None
        if self.detector_type == "MTCNN":
            # print(len(frames))
            # print(type(frames[0]))
            # exit()
            batch_boxes, *_ = self.detector.detect(frames, landmarks=False)
            # print(batch_boxes.shape)
            # exit()
        if self.detector_type == "face_recognition":
            results = []
            for frame in frames:
                batch_box = self.detector.face_locations(np.array(frame))
                ymin, xmax, ymax, xmin = [b for b in batch_box[0]]
                # print(batch_box)
                # print(type(batch_box[0]))
                batch_box[0] = (xmin, ymin, xmax, ymax)
                # print(batch_box)
                # print(type(batch_box[0]))
                # exit()
                print(batch_box)
                results.append(batch_box)
            batch_boxes = np.stack(results, axis=0)
        #     print(batch_boxes.shape)
        #     exit()
        # exit()
        return [b.tolist() if b is not None else None for b in batch_boxes]

    @ property
    def _batch_size(self):
        return 32


class VideoDataset(Dataset):

    def __init__(self, videos) -> None:
        super().__init__()
        self.videos = videos

    def __getitem__(self, index: int):
        video = self.videos[index]
        capture = cv2.VideoCapture(video)
        frames_num = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = OrderedDict()
        for i in range(frames_num):
            capture.grab()
            success, frame = capture.retrieve()
            if not success:
                continue
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            frame = frame.resize(size=[s // 2 for s in frame.size])
            frames[i] = frame
        return video, list(frames.keys()), list(frames.values())

    def __len__(self) -> int:
        return len(self.videos)
