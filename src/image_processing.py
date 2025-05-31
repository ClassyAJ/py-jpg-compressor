from pathlib import Path
from PIL import Image, UnidentifiedImageError
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TaskID,
)

from src.config import SUPPORTED_FORMATS, ALL_FORMATS_KEYWORD
from src.ui import logger, console
from src.utils import get_pillow_save_options

try:
    import pillow_heif
except ImportError:
    logger.debug("pillow_heif not installed. HEIC/HEIF support will be unavailable.")
    pillow_heif = None


def find_image_files(input_dir: Path, input_format_details: dict) -> list[Path]:
    """Collects image files from the input directory based on the specified format."""
    files_to_process: list[str] = []

    if input_format_details["pillow_format"] == ALL_FORMATS_KEYWORD:
        for _, fmt_details_loop in SUPPORTED_FORMATS.items():
            if fmt_details_loop["pillow_format"] == "HEIF" and not pillow_heif:
                continue
            for suffix in fmt_details_loop["suffixes"]:
                files_to_process.extend(list(input_dir.glob(pattern=f"*{suffix}")))
    else:
        if input_format_details["pillow_format"] == "HEIF" and not pillow_heif:
            logger.error(
                (
                    "HEIC/HEIF input format selected, but pillow-heif library "
                    "is not installed or failed to load."
                )
            )
            return []

        for suffix in input_format_details["suffixes"]:
            files_to_process.extend(list(input_dir.glob(pattern=f"*{suffix}")))

    return sorted(list(set(files_to_process)))


def _process_single_image(
    input_path: Path,
    output_path: Path,
    output_pillow_format: str,
    output_is_apng: bool,
    quality: int,
    target_resolution: tuple[int, int] | None,
) -> bool:
    """Processes a single image: opens, resizes, converts mode, and saves."""
    try:
        with Image.open(fp=input_path) as img:
            original_mode: str = img.mode
            original_size: tuple[int] = img.size

            if target_resolution:
                img.thumbnail(size=target_resolution, resample=Image.Resampling.LANCZOS)
                logger.debug(
                    "Resized '%s' from %s to %s",
                    input_path.name,
                    original_size,
                    img.size,
                )

            if output_pillow_format == "JPEG":
                if img.mode in ("RGBA", "LA", "P"):
                    if img.mode == "P" and "transparency" in img.info:
                        img: Image.Image = img.convert(mode="RGBA")
                    img = img.convert(mode="RGB")
                    logger.debug(
                        "Converted '%s' mode from %s to RGB for JPEG.",
                        input_path.name,
                        original_mode,
                    )

            if output_is_apng and img.mode == "P" and "transparency" in img.info:
                img = img.convert(mode="RGBA")

            # HEIF images (especially from iPhones) are often in YCbCr.
            # For broad compatibility or if further Pillow processing is needed,
            # converting to RGB is probably a must before saving,
            # unless saving back to HEIF where YCbCr is fine.
            # Pillow-heif handles YCbCr input and can save it.
            # If converting to JPG/PNG from HEIF, Pillow will handle the mode conversion.
            # If saving to HEIF, keeping original mode (if YCbCr) might be preferable for quality.
            # For simplicity, I let Pillow manage mode conversions during save.
            # Example: If source is HEIF (YCbCr) and output is PNG, Pillow converts to RGB/RGBA.

            save_options: dict = get_pillow_save_options(
                output_pillow_format=output_pillow_format, quality=quality
            )
            is_animated_source: bool = getattr(img, "is_animated", False)
            if is_animated_source and output_pillow_format in [
                "GIF",
                "WEBP",
                "TIFF",
                "PNG",
                "HEIF",
            ]:
                frames: list[Image.Image] = []
                if output_pillow_format == "HEIF" and not pillow_heif:
                    logger.warning(
                        (
                            "Cannot save animated HEIF for '%s'; "
                            "pillow-heif not available. Saving first frame only."
                        ),
                        input_path.name,
                    )
                    img.save(output_path, format=output_pillow_format, **save_options)
                    return True

                try:
                    for i in range(img.n_frames):
                        img.seek(frame=i)
                        current_frame: Image.Image = img.copy()
                        if output_is_apng and current_frame.mode != "RGBA":
                            current_frame = current_frame.convert(mode="RGBA")
                        frames.append(current_frame)
                except EOFError:
                    pass

                if frames:
                    save_options["save_all"] = True
                    save_options["append_images"] = frames[1:]
                    save_options["duration"] = img.info.get("duration", 100)
                    save_options["loop"] = img.info.get("loop", 0)

                    frames[0].save(
                        output_path, format=output_pillow_format, **save_options
                    )
                    logger.debug(
                        "Saved animated image '%s' with {len(frames)} frames.",
                        output_path.name,
                    )
                else:
                    img.save(
                        fp=output_path, format=output_pillow_format, **save_options
                    )
            else:
                img.save(fp=output_path, format=output_pillow_format, **save_options)

            logger.debug("Successfully processed and saved: '%s'", output_path)
            return True

    except UnidentifiedImageError:
        logger.error(
            (
                "Skipped: Cannot identify image file '%s'. Corrupted, invalid,"
                " or HEIF/AVIF support missing (check pillow-heif installation)."
            ),
            input_path,
        )
    except AttributeError as exc:
        if "NoneType" in str(exc) and "pillow_heif" in str(exc).lower():
            logger.error(
                (
                    "Skipped: Error related to HEIF processing for '%s'. "
                    "pillow-heif might not be correctly loaded or installed: %s"
                ),
                input_path,
                exc,
            )
        else:
            logger.error(
                "Skipped: Attribute error for '%s': %s", input_path, exc, exc_info=False
            )
    except IOError as exc:
        logger.error("Skipped: Pillow I/O error for '%s': %s", input_path, exc)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "Skipped: Unexpected error for '%s': %s", input_path, exc, exc_info=False
        )
    return False


def run_batch_processing(
    files_to_process: list[Path],
    output_dir: Path,
    output_format_details: dict,
    output_file_extension: str,
    quality: int,
    target_resolution: tuple[int, int] | None,
) -> tuple[int, int]:
    """Processes a list of image files and shows a progress bar."""
    processed_count = 0
    error_count = 0
    output_pillow_format = output_format_details["pillow_format"]
    output_is_apng: bool = (
        output_format_details.get("pillow_format") == "PNG"
        and output_file_extension.lower() == ".apng"
    )

    if output_pillow_format == "HEIF" and not pillow_heif:
        logger.error(
            (
                "HEIC/HEIF output format selected, but pillow-heif library is not "
                "installed or failed to load. Cannot proceed with this output format."
            )
        )
        return 0, len(files_to_process)

    progress_columns: list = [
        SpinnerColumn(),
        TextColumn(text_format="[progress.description]{task.description}"),
        BarColumn(),
        TextColumn(text_format="[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        TextColumn(
            text_format="([progress.completed]{task.completed} of [progress.total]{task.total})"
        ),
    ]

    with Progress(*progress_columns, console=console, transient=False) as progress:
        task_id: TaskID = progress.add_task(
            description="Processing images...", total=len(files_to_process)
        )

        for input_path in files_to_process:
            progress.update(
                task_id=task_id,
                advance=1,
                description=f"Processing [blue]{input_path.name}[/blue]",
            )
            output_filename: str = f"{input_path.stem}{output_file_extension}"
            output_path: Path = output_dir / output_filename

            if _process_single_image(
                input_path=input_path,
                output_path=output_path,
                output_pillow_format=output_pillow_format,
                output_is_apng=output_is_apng,
                quality=quality,
                target_resolution=target_resolution,
            ):
                processed_count += 1
            else:
                error_count += 1
            progress.update(task_id=task_id, description="Processing images...")

    return processed_count, error_count
