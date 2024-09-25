import pathlib


def load_texts(file_path: pathlib.Path) -> list[str]:
    """テキストファイルを読み込んでリストにして返す"""
    texts = []
    with open(file_path) as f:
        for line in f:
            texts.append(line.strip())
    return texts


TEMPLATE_MESSAGES = load_texts(pathlib.Path(__file__).parent.parent / "Text" / "template_messages.txt")

TEMPLATE_QUESTIONS = load_texts(pathlib.Path(__file__).parent.parent / "Text" / "template_questions.txt")
