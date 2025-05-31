from pathlib import Path
from PIL import Image, UnidentifiedImageError, ImageSequence
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
    files_to_process: list[Path] = []

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
    force_aspect_ratio: bool,
) -> bool:
    """Processes a single image: opens, resizes, converts mode, and saves."""
    try:
        with Image.open(fp=input_path) as img:
            original_mode: str = img.mode
            original_size: tuple[int, int] = img.size

            resized_frames_for_animation: list[Image.Image] | None = None

            if target_resolution:
                if getattr(img, "is_animated", False) and img.n_frames > 1:
                    frames_in = list(ImageSequence.Iterator(img))
                    frames_out: list[Image.Image] = []
                    for frame_img_in in frames_in:
                        # convert palette animated GIF frames to RGBA
                        # before resize if they have transparency
                        # to preserve it correctly, especially if
                        # forcing aspect ratio.
                        frame_to_resize: Image.Image = (
                            frame_img_in.convert(mode="RGBA")
                            if frame_img_in.mode == "P"
                            else frame_img_in.copy()
                        )

                        if force_aspect_ratio:
                            resized_frame = frame_to_resize.resize(
                                size=target_resolution,
                                resample=Image.Resampling.LANCZOS,
                            )
                        else:
                            temp_frame: Image.Image = frame_to_resize.copy()
                            temp_frame.thumbnail(
                                size=target_resolution,
                                resample=Image.Resampling.LANCZOS,
                            )
                            resized_frame: Image.Image = temp_frame
                        frames_out.append(resized_frame)

                    if frames_out:
                        img = frames_out[0]
                        resized_frames_for_animation = frames_out
                        logger.debug(
                            (
                                "Resized %d frames of animated '%s' from "
                                "%s to %s (force_aspect_ratio: %s)"
                            ),
                            len(frames_out),
                            input_path.name,
                            original_size,
                            img.size,
                            force_aspect_ratio,
                        )
                else:
                    if force_aspect_ratio:
                        img = img.resize(
                            size=target_resolution, resample=Image.Resampling.LANCZOS
                        )
                    else:
                        img.thumbnail(
                            size=target_resolution, resample=Image.Resampling.LANCZOS
                        )
                    logger.debug(
                        "Resized '%s' from %s to %s (force_aspect_ratio: %s)",
                        input_path.name,
                        original_size,
                        img.size,
                        force_aspect_ratio,
                    )

            if output_pillow_format == "JPEG":
                # If the image (or its first frame) has alpha, convert to RGB
                if img.mode in ("RGBA", "LA", "P"):
                    # If palette mode, check for transparency info.
                    # For APNG/GIF, alpha is in the 'P' mode palette
                    # Try converting to RGBA first to correctly handle transparency
                    # before stripping to RGB.
                    if img.mode == "P" and "transparency" in img.info:
                        img: Image.Image = img.convert(mode="RGBA")

                    # If still RGBA or LA after potential P->RGBA conversion, convert to RGB
                    if img.mode in ("RGBA", "LA"):
                        img = img.convert(mode="RGB")
                        logger.debug(
                            "Converted '%s' mode from %s to RGB for JPEG.",
                            input_path.name,
                            original_mode,
                        )
                        if resized_frames_for_animation:
                            resized_frames_for_animation = [
                                f.convert("RGB") if f.mode in ("RGBA", "LA") else f
                                for f in resized_frames_for_animation
                            ]

            if output_is_apng and img.mode == "P" and "transparency" in img.info:
                img = img.convert(mode="RGBA")
                # HEIF images (especially from iPhones) are often in YCbCr.
                # For broad compatibility or if further Pillow processing is needed,
                # converting to RGB is probably a must before saving,
                # unless saving back to HEIF where YCbCr is fine.
                # Pillow-heif handles YCbCr input and can save it.
                # If converting to JPG/PNG from HEIF, Pillow will handle the mode conversion.
                # If saving to HEIF, keeping original mode (if YCbCr)
                # might be preferable for quality.
                # For simplicity, I let Pillow manage mode conversions during save.
                # Example: If source is HEIF (YCbCr) and output is PNG, Pillow converts to RGB/RGBA.
                if resized_frames_for_animation:
                    resized_frames_for_animation = [
                        (
                            f.convert(mode="RGBA")
                            if (f.mode == "P" and "transparency" in f.info)
                            else f
                        )
                        for f in resized_frames_for_animation
                    ]

            save_options: dict = get_pillow_save_options(
                output_pillow_format=output_pillow_format, quality=quality
            )

            is_saving_animated = bool(resized_frames_for_animation) or (
                getattr(img, "is_animated", False)
                and not resized_frames_for_animation
                and img.n_frames > 1
            )

            if is_saving_animated and output_pillow_format in [
                "GIF",
                "WEBP",
                "TIFF",
                "PNG",
                "HEIF",
            ]:
                if output_pillow_format == "HEIF" and not pillow_heif:
                    logger.warning()
                    img.save(output_path, format=output_pillow_format, **save_options)
                    return True

                save_options["save_all"] = True
                save_options["duration"] = img.info.get("duration", 100)
                save_options["loop"] = img.info.get("loop", 0)

                if resized_frames_for_animation:
                    save_options["append_images"] = resized_frames_for_animation[1:]
                else:
                    frames_to_save_orig: list[Image.Image] = []
                    for i in range(1, img.n_frames):
                        img.seek(frame=i)
                        current_frame: Image.Image = img.copy()
                        if (
                            output_is_apng
                            and current_frame.mode == "P"
                            and "transparency" in current_frame.info
                        ):
                            current_frame = current_frame.convert("RGBA")
                        elif output_pillow_format == "JPEG" and current_frame.mode in (
                            "RGBA",
                            "LA",
                            "P",
                        ):
                            if (
                                current_frame.mode == "P"
                                and "transparency" in current_frame.info
                            ):
                                current_frame = current_frame.convert("RGBA")
                            if current_frame.mode in ("RGBA", "LA"):
                                current_frame = current_frame.convert("RGB")
                        frames_to_save_orig.append(current_frame)
                    save_options["append_images"] = frames_to_save_orig
                    img.seek(0)

                img.save(fp=output_path, format=output_pillow_format, **save_options)
                num_frames_saved = (
                    len(resized_frames_for_animation)
                    if resized_frames_for_animation
                    else img.n_frames
                )
                logger.debug(
                    "Saved animated image '%s' with %d frames.",
                    output_path.name,
                    num_frames_saved,
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
    output_format_details: dict[str, str | tuple[str]],
    output_file_extension: str,
    quality: int,
    target_resolution: tuple[int, int] | None,
    force_aspect_ratio: bool,
) -> tuple[int, int]:
    """Processes a list of image files and shows a progress bar."""
    processed_count = 0
    error_count = 0
    output_pillow_format: str | tuple[str] = output_format_details["pillow_format"]
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

    custom_progress_columns: tuple[
        SpinnerColumn | TextColumn | BarColumn | TimeRemainingColumn | TimeElapsedColumn
    ] = (
        SpinnerColumn(),
        TextColumn(text_format="[progress.description]{task.description}"),
        BarColumn(),
        TextColumn(text_format="[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        TextColumn(
            text_format="Processed: [progress.completed]{task.completed}/{task.total}"
        ),
    )

    with Progress(
        *custom_progress_columns, console=console, transient=False
    ) as progress:
        task_id: TaskID = progress.add_task(
            description="Initializing...",
            total=len(files_to_process),
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
                force_aspect_ratio=force_aspect_ratio,
            ):
                processed_count += 1
            else:
                error_count += 1
    return processed_count, error_count
