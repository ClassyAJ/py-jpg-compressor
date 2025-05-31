# py-jpg-compressor - Image Compressor & Resizer CLI

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by Typer](https://img.shields.io/badge/built%20with-Typer-brightgreen?logo=typer)](https://typer.tiangolo.com)
[![Uses Pillow](https://img.shields.io/badge/uses-Pillow-lightblue)](https://python-pillow.org/)
[![Styled with Rich](https://img.shields.io/badge/styled%20with-Rich-pink)](https://github.com/Textualize/rich)

A robust and beautiful command-line interface (CLI) tool built with Python, Typer, Pillow, and Rich to compress and resize images. Supports a wide variety of image formats (although the name does hint something else :D), including animated images and HEIC/HEIF.

## Features

* **Wide Format Support:** Process and convert between popular image formats:
  * PNG
  * JPG/JPEG
  * WEBP (including animated)
  * GIF (including animated)
  * APNG (Animated PNG)
  * TIFF (including multi-frame)
  * BMP
  * HEIC/HEIF (requires `pillow-heif` and `libheif`, including animated HEIF)
* **Image Compression:** Control output quality for formats like JPEG, WebP, and HEIF.
* **Image Resizing:**
  * Specify target width and height.
  * Option to preserve the original aspect ratio (default, fits within specified dimensions).
  * Option to force exact dimensions, potentially altering the aspect ratio.
* **Batch Processing:** Process all matching images in an input directory.
* **Flexible Input:**
  * Specify a single input format (e.g., `png`, `jpg`).
  * Use `all` to process all supported image types found in the input directory.
* **Customizable Paths:** Specify input and output folders, with sensible defaults (`./input` and `./output`).
* **User-Friendly Interface:**
  * Clear, colored console output powered by Rich.
  * Progress bar for batch operations.
  * Helpful error messages and prompts.
* **Cross-Platform:** Runs on Windows, macOS, and Linux (wherever Python and dependencies can be installed).

## Prerequisites

* Python 3.12 or newer.
* `pip` (Python package installer).

**For HEIC/HEIF Support (Optional but Recommended):**

* The `pillow-heif` Python package.
* The `libheif` system library:
  * **Linux (Debian/Ubuntu):** `sudo apt-get install libheif-dev`
  * **Linux (Fedora):** `sudo dnf install libheif-devel`
  * **macOS (Homebrew):** `brew install libheif`
  * **Windows:** `pillow-heif` wheels often bundle `libheif`. If not, manual installation might be needed.

## Installation

1. **Clone the repository (or download the source code):**

    ```bash
    git clone git@github.com:ClassyAJ/py-jpg-compressor.git
    cd py-jpg-compressor
    ```

2. **Create a virtual environment (recommended):**

    ```bash
    python -m venv .venv
    # On Windows
    .\.venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    * `"typer"` includes `rich` for enhanced CLI output.
    * `pillow-heif` for HEIC/HEIF support.
    * `pillow` for everything else.

## Usage

**General Command Structure:**

```bash
python -m src.app [OPTIONS]
# or
python image_tool_cli.py [OPTIONS]
```

### Getting Help

To see all available options and commands:

```bash
python -m src.app --help
```

### Command-Line Options

* `--input-format, -i TEXT`: (Required) Input image format(s).
  * Use a specific format like `png`, `jpg`, `webp`, `heic`.
  * Use `all` to process all supported types found in the input folder.
  * Example: `--input-format png` or `--input-format all`
* `--output-format, -o TEXT`: (Required) Desired output image format.
  * Must be one of the supported formats (e.g., `jpg`, `png`, `webp`).
  * Example: `--output-format webp`
* `--quality INTEGER`: (Optional) Compression quality (0-100). Higher means better quality and larger file size. Applies to formats like JPEG, WebP, HEIF.
  * Default: `85`
  * Range: `0` to `100`
  * Example: `--quality 75`
* `--width, -W INTEGER`: (Optional) Desired output width in pixels.
  * If provided, `--height` must also be provided.
  * If unset (along with `--height`), the original resolution is kept.
  * Example: `--width 1920`
* `--height, -H INTEGER`: (Optional) Desired output height in pixels.
  * If provided, `--width` must also be provided.
  * If unset (along with `--width`), the original resolution is kept.
  * Example: `--height 1080`
* `--force-aspect-ratio / --preserve-aspect-ratio`: (Optional Flag)
  * Use `--force-aspect-ratio` if you want the image resized to the exact `--width` and `--height`, potentially distorting the original aspect ratio. Only applies if width and height are set.
  * Default is `--preserve-aspect-ratio` (or omitting the flag), which maintains the aspect ratio, fitting the image within the specified width and height.
* `--input-folder, -if PATH`: (Optional) Path to the input folder containing images.
  * Default: `./input` (a folder named `input` in the current working directory).
  * Example: `--input-folder /path/to/the/input`
* `--output-folder, -of PATH`: (Optional) Path to the output folder where processed images will be saved.
  * Default: `./output` (a folder named `output` will be created in the current working directory if it doesn't exist).
  * Example: `--output-folder /path/to/the/output`
* `--help`: Show help message and exit.

### Examples

1. **Convert all PNG images in the default `./input` folder to JPG in `./output` with default quality (85) and original resolution:**

    ```bash
    python -m src.app --input-format png --output-format jpg
    ```

    (The tool will prompt for required options if not provided)

2. **Convert all supported image types (`all`) from a custom input folder to WebP format in a custom output folder, with quality 75:**

    ```bash
    python -m src.app --input-format all --output-format webp --quality 75 --input-folder ./my_raw_images --output-folder ./my_webp_images
    ```

3. **Resize all JPEGs to fit within 800x600 pixels (preserving aspect ratio) and save as PNGs:**

    ```bash
    python -m src.app --input-format jpg --output-format png --width 800 --height 600
    ```

    If you specify a different aspect ratio based on the relative aspect ratio of the specified height and width it will automatically keep the aspect ratio and resize the bigger axis to the desired size.

    Example:

    This resizes an image with `1200x800` to `500x333` since --force-aspect-ratio is unset

    ```bash
    python -m src.app --input-format jpg --output-format png --width 500 --height 500
    ```

4. **Resize all HEIC images to *exactly* 1024x768 pixels (forcing aspect ratio, potentially distorting) and save as JPEGs with 90% quality:**

    ```bash
    python -m src.app --input-format heic --output-format jpg --width 1024 --height 768 --force-aspect-ratio --quality 90
    ```

    Currently there is no feature to cut a specific aspect ratio out of the original image. I will maybe add that in the future.

5. **Convert animated GIFs to animated WebP, keeping original size and setting quality to 80:**

    ```bash
    python -m src.app --input-format gif --output-format webp --quality 80
    ```

## Default Behavior

* **Input Folder:** If `--input-folder` is not specified, the tool looks for an `input` directory in the current working directory.
* **Output Folder:** If `--output-folder` is not specified, the tool creates an `output` directory in the current working directory and saves processed images there.
* **Quality:** Defaults to `85` if not specified.
* **Resolution:** Original resolution is maintained if `--width` and `--height` are not specified.
* **Aspect Ratio:** Preserved by default when resizing. Use `--force-aspect-ratio` to change this.

## Troubleshooting

* **`ModuleNotFoundError`:** Ensure you are in the correct directory and have activated your virtual environment (if using one). You might need to run it as a module: `python -m src.app ...`. I usually use it like this since I save myself a lot of headaches with relative imports.

* **HEIC/HEIF issues:**
  * Make sure `pillow-heif` is installed (`pip show pillow-heif` or `pip freeze | grep -i pillow-heif` on linux/MacOS).
  * Ensure the `libheif` system library is installed correctly for your OS.
  * The tool will log errors if it cannot process HEIC/HEIF files due to missing dependencies.
* **Permissions:** Ensure the script has read permissions for the input folder/files and write permissions for the output folder.
* **File Not Found:** Double-check paths to input/output folders. Typer's `resolve_path=True` (I enabled that in the log handler IIRC) helps by converting to absolute paths, which can be useful for debugging path issues in logs.

## Contributing

Suggestions are welcome! Please feel free to submit a Pull Request or open an Issue for bugs, or feature requests

Either create an issue and explain the problem or do the following:

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.
6. Don't expect me to immediately review or merge it :-)

## License

This project is licensed under the MIT License - see the `LICENSE` file for details. Do what you want with it, I honestly don't care.
