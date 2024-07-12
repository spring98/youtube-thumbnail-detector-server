import tensorflow as tf
import numpy as np
import time

# GPU 메모리 사용량 모니터링을 위한 함수
def print_gpu_memory_usage():
    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        info = tf.config.experimental.get_memory_info('GPU:0')
        print(f"GPU: {gpu} | Free memory: {info['current']} bytes | Peak memory: {info['peak']} bytes")

# 간단한 모델 생성 및 데이터 준비
model = tf.keras.applications.MobileNetV2(weights='imagenet', include_top=False, pooling='avg')
dummy_input = np.random.rand(1, 224, 224, 3).astype(np.float32)

# 예측 수행 전 GPU 메모리 사용량 확인
print("Before prediction:")
print_gpu_memory_usage()

# 예측 수행
start_time = time.time()
for _ in range(100):  # 여러 번 예측을 수행하여 메모리 사용량을 확인
    model.predict(dummy_input)
end_time = time.time()

# 예측 수행 후 GPU 메모리 사용량 확인
print("\nAfter prediction:")
print_gpu_memory_usage()

print(f"\nTotal prediction time: {end_time - start_time:.2f} seconds")