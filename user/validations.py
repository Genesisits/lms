import os

from lms import constants


def validate_image_extension(value):
    if not (value == "" or value == None):
        ext = os.path.splitext(value.name)[1]
        if not ext.lower() in constants.VALID_EXTENSIONS:
            raise Exception("Unsupported file extension.")
