from flask import Flask, render_template, request
from google.cloud import storage

import cv2
import os
from google.cloud import vision
from typing import Sequence

BUCKET_NAME = "" # Change this to your bucket name


app = Flask(__name__)

def analyze_image_from_local(
    image_uri: str,
    feature_types: Sequence,
) -> vision.AnnotateImageResponse:
    client = vision.ImageAnnotatorClient()

    with open(image_uri, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
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

def draw_bounding_box(source_image_path, dest_image_path, result):
    # Draw bounding box on image
    image = cv2.imread(source_image_path)

    for annotation in result.text_annotations:
        vertices = annotation.bounding_poly.vertices
        cv2.rectangle(image, (vertices[0].x, vertices[0].y), (vertices[2].x, vertices[2].y), (0, 255, 0), 2) 

    cv2.imwrite(dest_image_path, image)


@app.route("/", methods=['GET', 'POST'])
def root():
    return render_template('index.html')

@app.route("/image", methods=['GET', 'POST'])
def show_image():
    if request.method == 'POST':
        temp_filename = "./static/temp.jpg"
        result_filename = "./static/result.jpg"

        # Retrieve uploaded file
        f = request.files['image-file']
        f.save(temp_filename)

        # Connect to Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        # Download image from Cloud Storage
        # blob = bucket.blob("test3.jpg")
        # blob.download_to_filename(temp_filename)

        # Vision processing
        response = analyze_image_from_local(image_uri=temp_filename, feature_types=[vision.Feature.Type.TEXT_DETECTION])
        draw_bounding_box(source_image_path=temp_filename, dest_image_path=result_filename, result=response)

        # Upload result to Cloud Storage
        blob = bucket.blob(f.filename)
        blob.upload_from_filename(result_filename)

        # Cleanup
        os.remove(temp_filename)
    return render_template('image.html')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
