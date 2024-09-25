import os
import pathlib

import click
from pdf2image import convert_from_path

from src.config import settings
from src.logger import setup_logger

setup_logger()


@click.command()
def main() -> None:
    """PDF を画像に変換したうえで unity から参照できる path に配置する"""
    print("start converting PDF to images...")
    pdf_path = settings.PYTHON_SERVER_ROOT / "PDF" / "【編集用】東京都知事選挙2024マニフェストデック.pdf"
    output_folder = settings.AITUBER_3D_ROOT / "Assets" / "Resources" / "Slides" / "manifest_demo_PDF"

    # Example usage
    _pdf_to_images(pdf_path=pdf_path, output_folder=output_folder)
    print("done!")


def _pdf_to_images(
    *,
    pdf_path: pathlib.Path,
    output_folder: pathlib.Path,
) -> None:
    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Convert PDF to images
    images = convert_from_path(pdf_path)

    # Save each image
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f"slide_{i+1}.png")
        image.save(image_path, "PNG")
        print(f"Saved {image_path}")


if __name__ == "__main__":
    main()
