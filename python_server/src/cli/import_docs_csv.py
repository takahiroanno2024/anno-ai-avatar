import csv

import click
import neologdn
import PyPDF2
import regex as re

from src.config import settings
from src.logger import setup_logger

setup_logger()


@click.command()
def main() -> None:
    """PDFをテキストにしてcsvにまとめる"""
    # pdf_path = settings.PYTHON_SERVER_ROOT / "PDF" / "【公開】東京都知事選2024安野たかひろマニフェスト（詳細版）v1.0.pdf"
    pdf_path = settings.PYTHON_SERVER_ROOT / "PDF" / "【編集用】東京都知事選挙2024マニフェストデック.pdf"
    docs_path = settings.PYTHON_SERVER_ROOT / "Text" / "政策　全体ストーリー（随時更新）.txt"
    output_path = settings.PYTHON_SERVER_ROOT / "faiss_knowledge" / "manifesto_demo_slides.csv"
    slide_path = settings.PYTHON_SERVER_ROOT / "faiss_knowledge" / "auto_generated.csv"
    text_list = _extract_text_from_pdf(pdf_path)
    docs_list = _convert_docs_to_csv(docs_path)
    merged_list = [["title", "text", "filename"]]
    memory = 0
    for jdx, j in enumerate(docs_list):
        updated = False
        print(jdx)
        doc_title = neologdn.normalize(re.sub(r"[\s\n]", "", j[0]))
        print(doc_title)
        if "皆様へのお願い" in j[0]:
            continue
        for idx, i in enumerate(text_list[memory:]):
            text_title = i[0]
            text_content = i[1]
            if doc_title in text_title or doc_title in text_content:
                merged_list.append([j[0], j[1], i[2]])
                updated = True
                memory += idx + 1
                break
        if not updated:
            for i in text_list:
                text_title = i[0].strip()
                text_content = i[1].strip()
                if j[0] in text_title or j[0] in text_content:
                    merged_list.append([j[0], j[1], i[2]])
                    updated = True
                    break
            if not updated:
                merged_list.append([j[0], j[1], "slide_1.png"])
    with open(output_path, "w") as f:
        write = csv.writer(f)
        write.writerows(merged_list)

    with open(slide_path, "w") as f:
        write = csv.writer(f)
        write.writerows(text_list)


def _convert_docs_to_csv(docs_path):
    with open(docs_path) as file:
        cont = file.read()
    cont = re.sub(r"\[a-z\]", "", cont)
    docs = re.split(r"\n\* ", cont)
    docs[0] = re.sub(r"\* ", "", docs[0]).strip()
    docs_list = [(i.split("\n")[0].strip(), i.strip()) for i in docs]
    return docs_list


def _extract_text_from_pdf(pdf_path):
    # PDFファイルを開く
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        # テキストを格納するためのリスト
        text_list = []
        # 各ページのテキストを読み取る
        for ids, page in enumerate(pdf_reader.pages, 1):
            filename = f"slide_{ids}.png"
            content = page.extract_text()
            text = neologdn.normalize(re.sub(r"[\s\n]", "", content.strip()))
            title = neologdn.normalize(re.sub(r"[\s\n]", "", content.split("\n")[0].strip()))
            if len(text) < 2:
                continue
            text_list.append([title, text, filename])

    return text_list


if __name__ == "__main__":
    main()
