import numpy as np
from PIL import Image
import tensorflow as tf
from io import BytesIO

# Load model once at startup
model = tf.keras.applications.MobileNetV2(
    weights='imagenet',
    input_shape=(224, 224, 3)
)

def predict_image(image_bytes: bytes) -> str:
    """Predict top class from image bytes"""
    # Preprocess image
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(
        img_array[np.newaxis, ...]
    )

    # Predict
    predictions = model.predict(img_array)
    decoded = tf.keras.applications.mobilenet_v2.decode_predictions(
        predictions, top=1
    )[0][0]

    return decoded[1]  # Return class name (e.g., 'lion')