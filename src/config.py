from pathlib import Path

APP_NAME = "py-image-compressor"
DEFAULT_QUALITY = 85
DEFAULT_INPUT_DIR_NAME = "input"
DEFAULT_OUTPUT_DIR_NAME = "output"
ALL_FORMATS_KEYWORD = "all"

SUPPORTED_FORMATS: dict[str, dict[str, str | tuple[str]]] = {
    "png": {"pillow_format": "PNG", "suffixes": (".png",)},
    "jpg": {"pillow_format": "JPEG", "suffixes": (".jpg", ".jpeg", ".jfif", ".jpe")},
    "jpeg": {"pillow_format": "JPEG", "suffixes": (".jpg", ".jpeg", ".jfif", ".jpe")},
    "webp": {"pillow_format": "WEBP", "suffixes": (".webp",)},
    "tiff": {"pillow_format": "TIFF", "suffixes": (".tiff", ".tif")},
    "bmp": {"pillow_format": "BMP", "suffixes": (".bmp",)},
    "gif": {"pillow_format": "GIF", "suffixes": (".gif",)},
    "apng": {
        "pillow_format": "PNG",
        "suffixes": (".png", ".apng"),
    },
    "heic": {"pillow_format": "HEIF", "suffixes": (".heic",)},
    "heif": {
        "pillow_format": "HEIF",
        "suffixes": (".heif", ".avif"),
    },
}

DEFAULT_INPUT_PATH: Path = Path(Path.cwd(), DEFAULT_INPUT_DIR_NAME)
DEFAULT_OUTPUT_PATH: Path = Path(Path.cwd(), DEFAULT_OUTPUT_DIR_NAME)
