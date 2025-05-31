from pathlib import Path

import typer

from src.ui import print_error
from src.config import SUPPORTED_FORMATS, ALL_FORMATS_KEYWORD


def get_pillow_save_options(output_pillow_format: str, quality: int) -> dict:
    """Returns a dictionary of options suitable for Pillow's Image.save() method."""
    options: dict[str, str | bool] = {}
    if output_pillow_format in ["JPEG", "WEBP", "HEIF"]:
        options["quality"] = quality
    if output_pillow_format == "PNG":
        options["optimize"] = True
    return options


def validate_and_get_format_details(
    format_str: str, format_type: str = "output"
) -> dict[str, str | tuple[str]]:
    """Validates format string and returns its details from SUPPORTED_FORMATS."""
    normalized_format_str: str = format_str.lower().lstrip(".")
    if format_type == "input" and normalized_format_str == ALL_FORMATS_KEYWORD:
        return {
            "pillow_format": ALL_FORMATS_KEYWORD,
            "suffixes": (ALL_FORMATS_KEYWORD,),
        }

    if normalized_format_str not in SUPPORTED_FORMATS:
        print_error(
            message=f"Unsupported {format_type} format: '{format_str}'.\n"
            f"Supported formats are: {', '.join(SUPPORTED_FORMATS.keys())}. "
            f"For all input types, use '{ALL_FORMATS_KEYWORD}'."
        )
        raise typer.Exit(code=1)
    return SUPPORTED_FORMATS[normalized_format_str]


def ensure_directory_exists(dir_path: Path, dir_type: str = "output") -> Path:
    """Ensures a directory exists, creating it if necessary, or validates if it's an input dir."""
    if dir_type == "input":
        if not dir_path.exists():
            print_error(message=f"Input folder not found: '{dir_path}'")
            raise typer.Exit(code=1)
        if not dir_path.is_dir():
            print_error(message=f"Input path is not a directory: '{dir_path}'")
            raise typer.Exit(code=1)
    else:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print_error(
                message=f"Could not create {dir_type} folder: '{dir_path}'. {e}"
            )
            raise typer.Exit(code=1)
    return dir_path
