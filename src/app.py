from pathlib import Path
from typer import Typer, Option, Exit
from typing_extensions import Annotated
from rich.markup import escape as escape_markup

from src import config
from src import ui
from src import utils
from src.image_processing import find_image_files, run_batch_processing

app: Typer = Typer(
    name=config.APP_NAME,
    help="A CLI tool to compress and resize images.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.command(no_args_is_help=True)
def process(
    input_format_str: Annotated[
        str,
        Option(
            "--input-format",
            "-i",
            help=(
                f"Input image format(s). Use '{config.ALL_FORMATS_KEYWORD}' "
                "for all supported, or e.g., 'png', 'jpg'."
            ),
            prompt=f"Enter input format ({config.ALL_FORMATS_KEYWORD}, png, jpg, etc.)",
        ),
    ],
    output_format_str: Annotated[
        str,
        Option(
            "--output-format",
            "-o",
            help="Output image format (e.g., 'jpg', 'webp', 'png', 'apng', 'heic').",
            prompt="Enter desired output format (jpg, png, webp, etc.)",
        ),
    ],
    quality: Annotated[
        int,
        Option(
            min=0,
            max=100,
            help="Compression quality (0-100). Higher quality, larger file.",
        ),
    ] = config.DEFAULT_QUALITY,
    width: Annotated[
        int | None,
        Option(
            "--width",
            "-W",
            help=(
                "Desired output width in pixels. If provided, --height must also "
                "be provided. If unset, original resolution is kept."
            ),
            min=1,
        ),
    ] = None,
    height: Annotated[
        int | None,
        Option(
            "--height",
            "-H",
            help=(
                "Desired output height in pixels. If provided, --width must also "
                "be provided. If unset, original resolution is kept."
            ),
            min=1,
        ),
    ] = None,
    force_aspect_ratio: Annotated[
        bool,
        Option(
            "--force-aspect-ratio/--preserve-aspect-ratio",
            help=(
                "Force resize to exact width and height, potentially changing aspect ratio. "
                "Only applies if --width and --height are set. "
                "Defaults to preserving aspect ratio."
            ),
        ),
    ] = False,
    input_dir_path: Annotated[
        Path | None,
        Option(
            "--input-folder",
            "-if",
            help=f"Path to input folder. Defaults to './{config.DEFAULT_INPUT_DIR_NAME}'.",
            resolve_path=True,
        ),
    ] = None,
    output_dir_path: Annotated[
        Path | None,
        Option(
            "--output-folder",
            "-of",
            help=(
                f"Path to output folder. Defaults to './{config.DEFAULT_OUTPUT_DIR_NAME}'. "
                "Created if not exists."
            ),
            resolve_path=True,
        ),
    ] = None,
) -> None:
    """
    Compresses and/or resizes images from an input folder to an output folder.
    Supports formats: PNG, JPG/JPEG, WEBP, TIFF, BMP, GIF, APNG, HEIC/HEIF (requires pillow-heif).
    Use '--input-format all' to process all supported input types.
    To resize, specify --width AND --height. Use --force-aspect-ratio to distort if needed.
    """
    ui.print_rule(title=f"{config.APP_NAME}")

    input_format_details: dict[str, str | tuple[str]] = (
        utils.validate_and_get_format_details(
            format_str=input_format_str, format_type="input"
        )
    )
    output_format_details: dict[str, str | tuple[str]] = (
        utils.validate_and_get_format_details(
            format_str=output_format_str, format_type="output"
        )
    )

    output_file_extension: str = output_format_details["suffixes"][0]

    target_resolution: tuple[int, int] | None = None
    if width is not None and height is not None:
        target_resolution = (width, height)
    elif width is not None or height is not None:
        ui.print_error(
            message="If resizing, both --width and --height must be specified."
        )
        ui.console.print(
            "If you do not want to resize, omit both --width and --height."
        )
        raise Exit(code=1)

    if force_aspect_ratio and not target_resolution:
        ui.print_warning(
            message="--force-aspect-ratio is specified, but --width and --height are not. "
            "The flag will be ignored."
        )
    actual_input_dir: Path = (
        input_dir_path if input_dir_path else config.DEFAULT_INPUT_PATH
    )
    actual_output_dir: Path = (
        output_dir_path if output_dir_path else config.DEFAULT_OUTPUT_PATH
    )

    utils.ensure_directory_exists(dir_path=actual_input_dir, dir_type="input")
    utils.ensure_directory_exists(dir_path=actual_output_dir, dir_type="output")

    ui.print_info(message=f"Input folder: '{actual_input_dir.resolve()}'")
    ui.print_info(message=f"Output folder: '{actual_output_dir.resolve()}'")
    ui.print_info(message=f"Input format filter: '{input_format_str}'")
    ui.print_info(
        message=(
            f"Output format: {output_format_details['pillow_format']} "
            f"(as {output_file_extension})"
        )
    )
    ui.print_info(message=f"Quality: {quality}")

    if target_resolution:
        w_str: str = f"[repr.number]{target_resolution[0]}[/repr.number]"
        h_str: str = f"[repr.number]{target_resolution[1]}[/repr.number]"

        resize_mode_text: str = (
            "exact (aspect ratio forced)"
            if force_aspect_ratio
            else "fit (aspect ratio preserved)"
        )
        message_string: str = (
            f"Target resolution: {w_str}x{h_str} "
            f"\\[{escape_markup(markup=resize_mode_text)}]"
        )
        ui.print_info(message=message_string)

    else:
        ui.print_info(message="Target resolution: Original")

    files_to_process: list[Path] = find_image_files(
        input_dir=actual_input_dir, input_format_details=input_format_details
    )

    if not files_to_process:
        ui.print_warning(
            message=f"No images found matching criteria in '{actual_input_dir}'."
        )
        raise Exit()

    ui.console.print(f"Found [cyan]{len(files_to_process)}[/cyan] image(s) to process.")

    processed_count, error_count = run_batch_processing(
        files_to_process=files_to_process,
        output_dir=actual_output_dir,
        output_format_details=output_format_details,
        output_file_extension=output_file_extension,
        quality=quality,
        target_resolution=target_resolution,
        force_aspect_ratio=(force_aspect_ratio if target_resolution else False),
    )

    ui.print_rule(title="Processing Complete")
    summary_color: str = (
        "green"
        if error_count == 0 and processed_count > 0
        else "yellow" if processed_count > 0 else "red"
    )

    ui.console.print(
        (
            f"[{summary_color}]Summary: {processed_count} image(s)"
            f" processed successfully.[/{summary_color}]"
        )
    )
    if error_count > 0:
        ui.print_error(
            message=f"Encountered errors with {error_count} image(s). Check logs above for details."
        )

    if processed_count == 0 and error_count == 0 and files_to_process:
        ui.print_warning(
            message=(
                "No images were processed. This might indicate an issue with "
                "filter criteria or an internal logic error."
            )
        )

    if processed_count == 0 and error_count > 0:
        ui.print_error(message="No images were processed successfully.")


if __name__ == "__main__":
    app()
