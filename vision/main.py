import cv2
import os
from google.cloud import vision
from typing import Sequence

SOURCE = "images"
PATH_OSCAR = "test.jpg"
PATH_FLORIST = "test2.jpg"
PATH_CAFE = "test3.jpg"
PATH_HTML = "image2.jpg"
FEATURES = [vision.Feature.Type.TEXT_DETECTION]


# Tutorial: https://codelabs.developers.google.com/codelabs/cloud-vision-api-python
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

def draw_bounding_box(image_path, result):
    # Draw bounding box on image
    image = cv2.imread(os.path.join(SOURCE, image_path))
    for annotation in result.text_annotations:
        vertices = annotation.bounding_poly.vertices
        cv2.rectangle(image, (vertices[0].x, vertices[0].y), (vertices[2].x, vertices[2].y), (0, 255, 0), 2) 

    cv2.imwrite(image_path, image)


# ----------------------------------------------
# 1. Draw bounding box
# ----------------------------------------------
image_path = PATH_OSCAR

# Use Cloud Vision to detect text
result = analyze_image_from_local(os.path.join(SOURCE, image_path), feature_types=FEATURES)
print_text(result)
draw_bounding_box(image_path, result)

# ----------------------------------------------
# 2. Edit word art image then draw bounding box
# ----------------------------------------------
image_path = PATH_FLORIST

# # Read image in grayscale
image = cv2.imread(os.path.join(SOURCE, image_path), cv2.IMREAD_GRAYSCALE)
# Floodfill background with white (255)
cv2.floodFill(image, None, seedPoint=(0, 0), newVal=255, loDiff=1, upDiff=1)
# If a pixel is not white (255), set it to black (0)
image[image != 255] = 0
# Save edited image
cv2.imwrite("temp.jpg", image)

# Use Cloud Vision to detect text
result = analyze_image_from_local("temp.jpg", feature_types=FEATURES)
print_text(result)
draw_bounding_box(image_path, result)
os.remove("temp.jpg")
