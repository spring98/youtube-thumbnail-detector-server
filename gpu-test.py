import tensorflow as tf

# Check for tensorflow GPU acess
print("TensorFlow has access to the following devices:", tf.config.list_physical_devices())

# See TensorFlow version
print("TensorFlow version:", tf.__version__)
# TensorFlow has access to the following devices: PhysicalDevice(name='/physical_device:CPU:0', device_type='CPU'), PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')
# TensorFlow version: 2.9.0