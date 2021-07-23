from django.core.exceptions import ValidationError
from lms.constants import VIDEO_EXTENSIONS, VIDEO_ERR_MSG


def validate_file_extension(value):
    """
    Function to validate the file extensions matching or not.
    File should be 12 MB if the file is a video file, or it should be 3 MB if it was other format.
    :param value: Video/Material file object..
    :return: Validation error/ None
    """
    if value.name.endswith(VIDEO_EXTENSIONS):
        if value.size > 4294967296:
            raise Exception(VIDEO_ERR_MSG.format(mb="12mb"))
    else:
        if value.size > 4294967296:
            raise Exception(VIDEO_ERR_MSG.format(mb="3mb"))
