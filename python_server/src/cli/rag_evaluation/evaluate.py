import asyncio
import csv
import json
import logging
import os
import pathlib
import re
import typing

import click
import google.generativeai as genai
from pydantic import BaseModel

from src.cli.loaders.qa_dataset import load_qa_dataset, split_qa_data_train_test
from src.cli.wrap.sync import sync
from src.config import settings
from src.gpt import DocumentRetrievalType, generate_response
from src.logger import setup_logger

setup_logger()

LOGGER = logging.getLogger(__name__)

genai.configure(api_key=settings.GOOGLE_API_KEY)
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY


class JudgeInput(BaseModel):
    """評価のための情報"""

    # 質問(ユーザー入力)
    input_text: str
    # 回答例
    example_output_text: str
    # 評価観点
    eval_aspect_text: str
    # 期待するスライドのページ
    eval_aspect_slide_number: list[int] | None


class ModelResponse(BaseModel):
    """モデルの応答"""

    response_text: str
    image_filename: str

    @property
    def filenumber(self) -> int:
        """ファイル名からスライドのページを取得する

        例: slide_13.png -> 13
        """
        return int(self.image_filename.split("_")[1].split(".")[0])


class JudgeResult(BaseModel):
    """応答の評価結果"""

    eval_text_score: int
    eval_slide_score: int
    reason: str

    judge_input: JudgeInput
    response: ModelResponse


@click.command()
@click.option(
    "--input-csv",
    "-i",
    type=click.Path(exists=True, path_type=pathlib.Path),
    required=True,
    help="Path to the downloaded CSV file from the Google Spreadsheet",
    default=pathlib.Path("qa_datasets", "ブロードリスニング用想定FAQ_ver0.1 - faq.csv"),
)
@click.option("--doc-retrieval-type", "-d", type=DocumentRetrievalType, help="Document retrieval type", default=DocumentRetrievalType.multi)
@click.option("--question-column-name-prefix", "-q", type=str, required=True, help="Prefix of the column name for questions", default="具体の質問")
@click.option("--answer-column-name-prefix", "-a", type=str, required=True, help="Prefix of the column name for answers", default="回答案")
@click.option("--eval-aspect-name-prefix", "-e", type=str, required=True, help="Prefix of the column name for evaluation aspect", default="評価観点")
@click.option("--eval-aspect-slide-number-column-prefix", "-s", type=str, required=True, help="Prefix of the column name for slide number", default="期待するスライドのページ")
@click.option("--use-all", "-a", is_flag=True, help="Use all data for evaluation", default=False)
@click.option("--random-state", "-r", type=int, help="Random seed", default=42)
@click.option("--test-size", "-t", type=float, help="Test size ratio", default=0.2)
@click.option("--output-path", "-o", type=click.Path(path_type=pathlib.Path), help="Path to the output dataset", default=settings.PYTHON_SERVER_ROOT / "log" / "evaluation_result.csv")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging", default=False)
@sync
async def main(
    input_csv: pathlib.Path,
    doc_retrieval_type: DocumentRetrievalType,
    question_column_name_prefix: str,
    answer_column_name_prefix: str,
    eval_aspect_name_prefix: str,
    eval_aspect_slide_number_column_prefix: str,
    use_all: bool,
    random_state: int,
    test_size: float,
    output_path: pathlib.Path,
    debug: bool,
) -> None:
    """指定したCSVを読み込んでモデルの評価を行う

    input_csv: 評価対象のCSVファイルへの path. 内部的にGoogle Spreadsheetで管理しているQ&A集からダウンロードしたCSVを想定。

    評価時には事前に RAG の DB の更新を行い、評価セットと RAG の状態を一致させてください。

    以下の順で行う
        1. CSV を読み込んで回答の生成、及び表示するスライドの指定を行う
        2. それぞれを評価する

    生成したテキストと指示するスライド番号をそれぞれ評価する。
    生成したテキストは1点(最低)～5点(最高)の5段階評価を行う。
    スライド番号は、指定されたスライド番号に含まれている場合は5点、含まれていない場合は1点とする。

    入力の CSV ファイルのフォーマット: 内部的にGoogle Spreadsheetで管理しているQ&A集からダウンロードしたCSVを想定。適宜 *-column-name-prefixオプションで列名を指定。

    出力の CSV ファイルのフォーマット

    | input_text | example_output_text | eval_aspect_text | eval_aspect_slide_number            | generated_text | eval_text_score | eval_slide_score | reason |
    |------------|---------------------|------------------|-------------------------------------|----------------|-----------------|------------------|--------|
    | 質問       | 回答例              | 評価観点         | 期待するスライドのページ(list[int]) | 生成した回答文 | int             | int              | str    |

    """
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    dataset = load_qa_dataset(
        input_csv=input_csv,
        question_column_name_prefix=question_column_name_prefix,
        answer_column_name_prefix=answer_column_name_prefix,
        eval_aspect_name_prefix=eval_aspect_name_prefix,
        eval_aspect_slide_number_column_prefix=eval_aspect_slide_number_column_prefix,
    )
    if use_all:
        test_set = dataset
    else:
        _, test_set = split_qa_data_train_test(dataset, test_size=test_size, random_state=random_state)
    judge_inputs = [
        JudgeInput(
            input_text=qa.question,
            example_output_text=qa.answer,
            eval_aspect_text=qa.eval_aspect_text,
            eval_aspect_slide_number=qa.eval_aspect_slide_number,
        )
        for qa in test_set
    ]
    LOGGER.info(f"評価対象の質問数: {len(judge_inputs)}")
    LOGGER.debug(f"評価対象の質問:\n{judge_inputs}")
    await _evaluate(judge_inputs=judge_inputs, output_dataset_path=output_path, doc_retrieval_type=doc_retrieval_type)


async def _evaluate(
    judge_inputs: list[JudgeInput],
    output_dataset_path: pathlib.Path,
    doc_retrieval_type: DocumentRetrievalType = DocumentRetrievalType.multi,
) -> None:
    """CSV を読み込んで回答の生成、及び表示するスライドの指定を行う"""
    judge_results: list[JudgeResult] = []

    tasks = [_evaluate_row(judge_input=judge_input, doc_retrieval_type=doc_retrieval_type) for judge_input in judge_inputs]

    for result in await asyncio.gather(*tasks):
        judge_results.append(result)

    print("評価結果")
    print("#################")

    for judge_result in judge_results:
        print(f"質問: {judge_result.judge_input.input_text}")
        print(f"回答例: {judge_result.judge_input.example_output_text}")
        print(f"評価観点: {judge_result.judge_input.eval_aspect_text}")
        print(f"生成した回答文: {judge_result.response.response_text}")
        print(f"テキストの評価: {judge_result.eval_text_score}")
        print(f"スライドの評価: {judge_result.eval_slide_score}")
        print(f"評価理由: {judge_result.reason}")
        print("#################")

    # 結果を CSV or MD に書き込む
    result_dicts = [
        {
            "input_text": judge_result.judge_input.input_text,
            "example_output_text": judge_result.judge_input.example_output_text,
            "eval_aspect_text": judge_result.judge_input.eval_aspect_text,
            "eval_aspect_slide_number": judge_result.judge_input.eval_aspect_slide_number,
            "generated_text": judge_result.response.response_text,
            "eval_text_score": judge_result.eval_text_score,
            "eval_slide_score": judge_result.eval_slide_score,
            "reason": judge_result.reason,
        }
        for judge_result in judge_results
    ]

    with output_dataset_path.open(mode="w", newline="") as f:
        if output_dataset_path.suffix == ".md":
            _write_list_dict_to_md_table(result_dicts, f)
        else:
            writer = csv.DictWriter(
                f,
                fieldnames=list(result_dicts[0].keys()),
            )

            writer.writeheader()

            for result_dict in result_dicts:
                writer.writerow(result_dict)

    # 出力 path の表示
    print(f"出力先: {output_dataset_path}")


async def _evaluate_row(judge_input: JudgeInput, doc_retrieval_type: DocumentRetrievalType = DocumentRetrievalType.multi):
    response_text, image_filename = await generate_response(
        text=judge_input.input_text,
        skip_logging=True,
        doc_retrieval_type=doc_retrieval_type,
    )

    model_reponse = ModelResponse(
        response_text=response_text,
        image_filename=image_filename,
    )

    prompt = _prompt_for_eval.format(
        input_text=judge_input.input_text,
        example_output_text=judge_input.example_output_text,
        eval_aspect_text=judge_input.eval_aspect_text,
        pred=model_reponse.response_text,
    )

    response = await _async_generate_response(prompt)

    _validate_reponse(response)

    if judge_input.eval_aspect_slide_number is None:
        eval_slide_score = 5  # スライドの評価が指定されていない場合は最高点
    else:
        eval_slide_score = 5 if model_reponse.filenumber in judge_input.eval_aspect_slide_number else 1

    return JudgeResult(
        eval_text_score=response["grade"],
        eval_slide_score=eval_slide_score,
        reason=response["reason"],
        judge_input=judge_input,
        response=model_reponse,
    )


async def _async_generate_response(prompt: str):
    model = genai.GenerativeModel("gemini-1.5-pro", generation_config={"response_mime_type": "application/json"})
    response = await model.generate_content_async(prompt)
    json_reply = response.text
    try:
        return json.loads(json_reply).get("response", "")
    except Exception as e:
        print("---------------")
        print(json_reply)
        print("---------------")
        raise e


def _validate_reponse(response: dict) -> None:
    """response を JSON としてパースし、下記のスキーマに合致することを確かめる

    {"reason": "<評価理由>", "grade": <int, 1～5の5段階評価>}
    """
    if not isinstance(response, dict):
        raise ValueError("Response is not a JSON object")

    required_keys = {"reason", "grade"}

    if not required_keys.issubset(response.keys()):
        raise ValueError("Missing required keys")

    if not isinstance(response["reason"], str):
        raise ValueError("'reason' should be a string")

    if not isinstance(response["grade"], int) or not (1 <= response["grade"] <= 5):
        raise ValueError("'grade' should be an integer between 1 and 5")


# ELYZA-tasks-100 を参考に
_prompt_for_eval = """
あなたは言語モデルの採点者です。

YouTube のライブ配信で、東京都知事選挙に立候補している候補者の代わりに回答するモデルです。

問題, 正解例, 採点基準, 言語モデルが生成した回答が与えられます。

「採点基準」と「正解例」を参考にして、「言語モデルの回答」を評価してください。
そして、回答理由および1,2,3,4,5の5段階評価による採点結果を「評価フォーマット」に示すようなJSON形式で返してください。

# 問題
{input_text}

# 正解例
{example_output_text}

# 採点基準
基本的な採点基準
- 1点: 誤っている、 指示に従えていない
- 2点: 誤っているが、方向性は合っている
- 3点: 部分的に誤っている、 部分的に合っている
- 4点: 合っている
- 5点: 役に立つ

基本的な減点項目
- 不自然な日本語: -1点
- 部分的に事実と異なる内容を述べている: -1点
- 「倫理的に答えられません」のように過度に安全性を気にしてしまっている: 2点にする

問題固有の採点基準
{eval_aspect_text}

# 言語モデルの回答
{pred}

# 評価フォーマット
{{"reason": "(採点基準に照らした評価内容)", "grade": (採点結果、1～5の5段階評価)}}
"""


def _escape_md_table_value(value):
    value = str(value)
    value = value.replace("\n", "<br>")
    value = re.sub(r"[|]", r"\|", value)
    return value


def _write_list_dict_to_md_table(data: list[dict], f: typing.TextIO):
    if not data:
        return

    headers = list(data[0].keys())
    escaped_headers = [re.sub(r"[_-]", " ", h) for h in headers]

    # Write table headers
    f.write(f"| {' | '.join(escaped_headers)} |\n")
    f.write(f"| {' | '.join(['---'] * len(headers))} |\n")

    # Write table rows
    for row in data:
        values = [_escape_md_table_value(row.get(header, "")) for header in headers]
        f.write(f"| {' | '.join(values)} |\n")


if __name__ == "__main__":
    main()
