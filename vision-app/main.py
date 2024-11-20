import base64
import cv2
import io
import numpy as np

from flask import Flask, render_template, request
from google.cloud import storage, vision
from PIL import Image
from typing import Sequence

BUCKET_NAME = "" # Change this to your bucket name


app = Flask(__name__)

def analyze_image_from_local(
    image_bytes: bytes,
    feature_types: Sequence,
) -> vision.AnnotateImageResponse:
    client = vision.ImageAnnotatorClient()

    image = vision.Image(content=image_bytes)
    features = [vision.Feature(type_=feature_type) for feature_type in feature_types]
    request = vision.AnnotateImageRequest(image=image, features=features)

    response = client.annotate_image(request=request)

    return response

def print_text(response: vision.AnnotateImageResponse):
    print("=" * 80)
    for annotation in response.text_annotations:
        vertices = [f"({v.x},{v.y})" for v in annotation.bounding_poly.vertices]
        print(
            f"{repr(annotation.description):42}",
            ",".join(vertices),
            sep=" | ",
        )

def draw_bounding_box(image_bytes, result):
    # Draw bounding box on image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    for annotation in result.text_annotations:
        vertices = annotation.bounding_poly.vertices
        cv2.rectangle(image, (vertices[0].x, vertices[0].y), (vertices[2].x, vertices[2].y), (0, 255, 0), 2) 

    _, encoded_image = cv2.imencode('.jpg', image)
    return encoded_image.tobytes()


@app.route("/", methods=['GET', 'POST'])
def root():
    return render_template('index.html')

@app.route("/image", methods=['GET', 'POST'])
def show_image():
    if request.method == 'POST':
        # Retrieve uploaded file
        f = request.files['image-file']
        image_bytes = f.read()

        # Connect to Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        # Download image from Cloud Storage
        # blob = bucket.blob("test3.jpg")
        # blob.download_to_filename(temp_filename)

        # Vision processing
        response = analyze_image_from_local(image_bytes=image_bytes, feature_types=[vision.Feature.Type.TEXT_DETECTION])
        result_bytes = draw_bounding_box(image_bytes=image_bytes, result=response)
        
        # Upload result to Cloud Storage
        blob = bucket.blob(f.filename)
        blob.upload_from_string(result_bytes, content_type='image/jpeg')

        # Save image as in-memory file
        img = Image.open(io.BytesIO(result_bytes))
        buffer = io.BytesIO()
        img.save(buffer, 'JPEG')
        encoded_img_data = base64.b64encode(buffer.getvalue())

    return render_template('image.html', image=encoded_img_data.decode('utf-8'))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
