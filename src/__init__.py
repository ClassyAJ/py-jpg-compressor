try:
    # Attempt to register HEIF support if pillow_heif is installed
    # The act of importing pillow_heif usually registers its openers with Pillow
    import pillow_heif
except ImportError:
    # pillow_heif is not installed if his exception is caught.
    # HEIC/HEIF support will therefore not be available.
    # The program will still run but will error if HEIC/HEIF is chosen as input/output
    # unless SUPPORTED_FORMATS is dynamically filtered in the future, or errors are
    # handled gracefully. The validation will catch unsupported formats if
    # pillow_heif isn't loaded and 'heic'/'heif' are requested.
    pass

from src import config
from src import image_processing
from src import ui
from src import utils
