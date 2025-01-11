"""
Converter and compressor for PNG to JPG images
"""

import os
from pathlib import Path
from PIL import Image


def convert_and_compress_images(
    input_folder: Path,
    output_folder: Path,
    target_size: tuple = (1920, 1080),
    quality: int = 85,
) -> None:
    """
    Converts PNG images to JPG, resizes them while keeping the original aspect ratio,
    compresses them, and saves them to the output folder. Also processes JPG images
    by resizing and compressing them if they are not already resized to the target size.
    """
    if not output_folder.exists():
        output_folder.mkdir(parents=True)

    for file_name in os.listdir(path=input_folder):
        if file_name.lower().endswith((".png", ".jpg")):
            input_path: Path = Path(input_folder, file_name)
            output_file_name: str = f"{input_path.stem}.jpg"
            output_path: Path = Path(output_folder, output_file_name)

            with Image.open(fp=input_path) as img:

                if img.size != target_size:
                    img.thumbnail(size=target_size)

                if file_name.lower().endswith(".png"):
                    img: Image.Image = img.convert(mode="RGB")

                img.save(fp=output_path, format="JPEG", quality=quality)
                print(f"Processed and saved: {output_path}")


current_dir: Path = Path(__file__).parent
convert_and_compress_images(
    input_folder=Path(current_dir, "input"),
    output_folder=Path(current_dir / "output"),
)
