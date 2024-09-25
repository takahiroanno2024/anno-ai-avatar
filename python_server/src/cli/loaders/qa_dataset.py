import csv
import logging
import pathlib

from pydantic import BaseModel

from src.logger import setup_logger

setup_logger()

LOGGER = logging.getLogger(__name__)


class QAData(BaseModel):
    """Q&Aデータ"""

    question: str
    answer: str
    eval_aspect_text: str | None
    eval_aspect_slide_number: list[int] | None


def split_qa_data_train_test(qa_dataset: list[QAData], test_size: float, random_state: int) -> tuple[list[QAData], list[QAData]]:
    """Q&Aデータを学習用とテスト用に分割する。

    テストデータは全て eval_aspect_text がNoneでないデータとなる（eval_aspect_textがNoneでないデータがテストデータセットのサイズに足りない時は、その数で打ち切る）。
    """
    from sklearn.model_selection import train_test_split

    qa_dataset_with_eval_aspect = [qa for qa in qa_dataset if qa.eval_aspect_text]
    qa_dataset_without_eval_aspect = [qa for qa in qa_dataset if not qa.eval_aspect_text]
    LOGGER.debug(f"qa_dataset_with_eval_aspect: {len(qa_dataset_with_eval_aspect)}")
    LOGGER.debug(f"qa_dataset_without_eval_aspect: {len(qa_dataset_without_eval_aspect)}")

    test_num = int(len(qa_dataset) * test_size)
    LOGGER.debug(f"test_num: {test_num}")

    if test_num > len(qa_dataset_with_eval_aspect):
        LOGGER.warning("テストデータセットのサイズが足りません。テストデータセットのサイズを調整します。")
        return qa_dataset_without_eval_aspect, qa_dataset_with_eval_aspect

    train_set_with_eval_aspect, test_set_with_eval_aspect = train_test_split(qa_dataset_with_eval_aspect, test_size=test_size, random_state=random_state)
    train_set = qa_dataset_without_eval_aspect + train_set_with_eval_aspect

    return train_set, test_set_with_eval_aspect


def load_qa_dataset(
    input_csv: pathlib.Path,
    question_column_name_prefix: str,
    answer_column_name_prefix: str,
    eval_aspect_name_prefix: str,
    eval_aspect_slide_number_column_prefix: str,
) -> list[QAData]:
    """CSVファイルからQ&Aデータを読み込む。内部的にGoogle Spreadsheetで管理しているQ&A集からダウンロードしたCSVを想定。"""
    with input_csv.open() as f:
        reader = csv.reader(f)

        header = next(reader)
        question_column_index = _get_column_index(header, question_column_name_prefix)
        answer_column_index = _get_column_index(header, answer_column_name_prefix)
        eval_aspect_column_index = _get_column_index(header, eval_aspect_name_prefix)
        eval_aspect_slide_number_column_index = _get_column_index(header, eval_aspect_slide_number_column_prefix)

        dataset = []
        for row in reader:
            question = row[question_column_index]
            answer = row[answer_column_index]
            eval_aspect_text = row[eval_aspect_column_index] or None
            eval_aspect_slide_number_str = row[eval_aspect_slide_number_column_index]
            eval_aspect_slide_number = [int(s) for s in eval_aspect_slide_number_str.split(",")] if eval_aspect_slide_number_str else None

            if not question or not answer:
                LOGGER.debug(f"空の行が見つかりました: {row}")
                continue

            dataset.append(
                QAData(
                    question=question,
                    answer=answer,
                    eval_aspect_text=eval_aspect_text,
                    eval_aspect_slide_number=eval_aspect_slide_number,
                )
            )
    LOGGER.info(f"読み込んだデータ数: {len(dataset)}")

    return dataset


def _get_column_index(header: list[str], prefix: str) -> int:
    candidate_indices = [(i, h) for i, h in enumerate(header) if h.startswith(prefix)]
    if len(candidate_indices) > 1:
        LOGGER.warning(f"カラム '{prefix}*' が複数見つかりました: {candidate_indices}")
    if len(candidate_indices) == 0:
        raise ValueError(f"カラム '{prefix}*' が見つかりませんでした")
    return candidate_indices[0][0]
