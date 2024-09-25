import csv

import click
import PyPDF2

from src.config import settings
from src.logger import setup_logger

setup_logger()


@click.command()
def main() -> None:
    """PDFをテキストにしてcsvにまとめる"""
    print("start converting PDF to csv...")
    pdf_path = settings.PYTHON_SERVER_ROOT / "PDF" / "【編集用】東京都知事選挙2024マニフェストデック.pdf"
    output_path = settings.PYTHON_SERVER_ROOT / "faiss_knowledge" / "auto_generated.csv"
    text_list = _extract_text_from_pdf(pdf_path)

    with open(output_path, "w") as f:
        write = csv.writer(f)
        write.writerows(text_list)
    print("done!")


def _extract_text_from_pdf(pdf_path):
    # PDFファイルを開く
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        # テキストを格納するためのリスト
        text_list = [["title", "text", "filename"]]
        # 各ページのテキストを読み取る
        for ids, page in enumerate(pdf_reader.pages, 1):
            filename = f"slide_{ids}.png"
            content = page.extract_text()
            title = content.split("\n")[0].strip()
            text = "".join(content.split("\n")[1:]).strip()
            if len(text) < 2:
                continue
            text_list.append([title, text, filename])

    return text_list


if __name__ == "__main__":
    main()
