import cv2
import numpy as np
import time
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications import MobileNetV3Small
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import tensorflow as tf

class ImageAnalyzer:
    def __init__(self, video_path, target_image_path, sampling_interval=30):
        # XLA 컴파일러 활성화
        tf.config.optimizer.set_jit(True)

        # GPU 사용 여부를 확인
        physical_devices = tf.config.experimental.list_physical_devices('GPU')
        if len(physical_devices) > 0:
            print("Using GPU:", physical_devices)
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
        else:
            print("No GPU found. Using CPU.")

        self.video_path = video_path
        self.target_image_path = target_image_path
        self.sampling_interval = sampling_interval

        self.model = MobileNetV3Small(weights='imagenet', include_top=False, pooling='avg')
        # self.model = MobileNetV3Small(weights='imagenet', include_top=False, pooling='avg', input_shape=(96, 96, 3))
        # self.model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

        self.target_image_features = self.extract_features(self.load_target_image())

    def load_target_image(self):
        img = image.load_img(self.target_image_path, target_size=(224, 224))
        # img = image.load_img(self.target_image_path, target_size=(96, 96))
        img_data = image.img_to_array(img)
        img_data = np.expand_dims(img_data, axis=0)
        img_data = preprocess_input(img_data)
        return img_data

    def extract_features(self, img_data):
        # features = self.model.predict(img_data)
        features = self.model.predict(img_data, batch_size=32)
        return features.flatten()

    def preprocess_frame(self, frame):
        frame = cv2.resize(frame, (224, 224))
        # frame = cv2.resize(frame, (96, 96))
        frame = image.img_to_array(frame)
        frame = np.expand_dims(frame, axis=0)
        frame = preprocess_input(frame)
        return frame

    def calculate_similarity(self, features1, features2):
        return cosine_similarity([features1], [features2])[0][0]

    def find_best_frame_in_range(self, cap, start_idx, end_idx, step, frame_rate):
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        best_similarity = -1
        best_frame_index = -1
        start_time = time.time()

        for frame_idx in range(start_idx, end_idx, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break

            frame_data = self.preprocess_frame(frame)
            frame_features = self.extract_features(frame_data)
            similarity = self.calculate_similarity(self.target_image_features, frame_features)

            if similarity > best_similarity:
                best_similarity = similarity
                best_frame_index = frame_idx

            if frame_idx % 2 == 0 or frame_idx == total_frames - 1:  # 매 2프레임마다 출력
                elapsed_time = time.time() - start_time
                progress = (frame_idx + 1) / total_frames
                estimated_total_time = elapsed_time / progress
                remaining_time = estimated_total_time - elapsed_time
                best_frame_time = best_frame_index / frame_rate

                print(f"Progress: {progress * 100:.2f}% | Elapsed Time: {elapsed_time:.2f}s "
                      f"| Best Similarity: {best_similarity:.2f} | Best FrameTime: {best_frame_time:.2f}s")

        return best_frame_index, best_similarity

    def find_most_similar_frame(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return None, None

        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / frame_rate

        if video_duration > 1800:  # 동영상 길이가 30분(1800초) 이상이면
            print("Video is longer than 20 minutes. Skipping analysis.")
            return None, -1

        start_time = time.time()

        # 샘플링된 프레임에서 가장 유사한 프레임을 찾기
        best_frame_index, best_similarity = self.find_best_frame_in_range(cap, 0, total_frames, self.sampling_interval, frame_rate)

        # 주변 프레임을 세밀하게 비교
        start_idx = max(0, best_frame_index - self.sampling_interval)
        end_idx = min(total_frames, best_frame_index + self.sampling_interval)
        best_frame_index, best_similarity = self.find_best_frame_in_range(cap, start_idx, end_idx, 1, frame_rate)

        elapsed_time = time.time() - start_time
        print(f"Total elapsed time: {elapsed_time:.2f}s")

        best_frame_time = best_frame_index / frame_rate

        # 해당 프레임 추출
        cap.set(cv2.CAP_PROP_POS_FRAMES, best_frame_index)
        ret, best_frame = cap.read()
        if not ret:
            print("Error: Could not read the best frame.")
            return None, None

        cap.release()

        return best_frame, best_frame_time

    def display_comparison(self, best_frame):
        best_frame_gray = cv2.cvtColor(best_frame, cv2.COLOR_BGR2GRAY)
        target_image_gray = cv2.imread(self.target_image_path, cv2.IMREAD_GRAYSCALE)

        # 타겟 이미지와 가장 유사한 프레임 시각적으로 비교
        plt.figure(figsize=(10, 5))

        plt.subplot(1, 2, 1)
        plt.title("Target Image")
        plt.imshow(target_image_gray, cmap='gray')

        plt.subplot(1, 2, 2)
        plt.title("Best Frame")
        plt.imshow(best_frame_gray, cmap='gray')

        plt.show()
