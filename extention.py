from flask_sqlalchemy import SQLAlchemy
import base64
db = SQLAlchemy()
# from sqlalchemy_imageattach.entity import Image, image_attachment

# Code from https://www.programcreek.com/2013/09/convert-image-to-string-in-python/


def image_to_str(filepath):
    with open(filepath, "rb") as imageFile:
        string = imageFile.read()
        return string

def str_to_image(filepath):
    image = open(filepath, "wb")
    image.write(str.decode('base64'))
    image.close()
    return image
