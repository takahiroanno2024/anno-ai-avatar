import csv
import datetime
import io
import json
import logging
import pathlib
import shutil
import subprocess
import sys
from logging.handlers import TimedRotatingFileHandler

import structlog


class JsonFormatter(logging.Formatter):
    """GPTLogRecord を JSON で出力するための Formatter"""

    def format(self, record: "GPTLogRecord"):
        """JSON 形式でログを出力する"""
        log_entry = {
            "timestamp": record.timestamp_.isoformat(),
            "doc_retrieval_type": record.doc_retrieval_type,
            "rag_qa": record.rag_qa,
            "rag_knowledge": record.rag_knowledge,
            "metadata": record.metadata_,
            "question": record.question,
            "response": record.response,
            "latency": record.latency,
        }
        return json.dumps(log_entry, ensure_ascii=False)


class CsvFormatter(logging.Formatter):
    """GPTLogRecord を CSV で出力するための Formatter"""

    def format(self, record: "GPTLogRecord"):
        """CSV 形式でログを出力する"""
        output = io.StringIO()
        csv_writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        log_entry = [
            record.timestamp_.isoformat(),
            record.doc_retrieval_type,
            record.rag_qa,
            record.rag_knowledge,
            record.metadata_,
            record.question,
            record.response,
            record.latency,
        ]

        csv_writer.writerow(log_entry)
        return output.getvalue().strip()


class GPTLogRecord(logging.LogRecord):
    """gpt の応答結果"""

    timestamp_: datetime.datetime
    doc_retrieval_type: str
    rag_qa: dict
    rag_knowledge: str
    metadata_: dict
    question: str
    response: str
    latency: float


class BaseGPTLogRecordTimedRotatingFileHandler(TimedRotatingFileHandler):
    """GPTLogRecord を 出力するための TimedRotatingFileHandler のベースクラス"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namer = self._custom_namer
        self.rotator = self.custom_rotator

    def doRollover(self) -> None:
        """ファイルをローテーションするときの動作(override)"""
        super().doRollover()
        self._upload_files()

    def _upload_files(self) -> None:
        """未アップロードのファイルを Google Drive にアップロードする"""
        command = ["poetry", "run", "python", "-m", "src.cli.upload_logs_to_google_drive"]

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)  # noqa: S603

            print("Command Output:\n", result.stdout)

            if result.stderr:
                print("Command Error Output:\n", result.stderr)

        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            print("Command Error Output:\n", e.stderr)

    def custom_rotator(self, source: str, dest: str) -> None:
        """files_to_upload/ 以下にファイルを移動しつつ、ローテーションを行う"""
        copy_to = pathlib.Path(self.baseFilename).parent / "files_to_upload" / pathlib.Path(dest).name

        # アップロード用のコピー
        print(f"Copying {source} to {copy_to}")
        shutil.copy(source, copy_to)

        # ローテーション
        print(f"Rotating {source} to {dest}")
        shutil.move(source, dest)

    def _custom_namer(self, default_name: str) -> str:
        original_csv_filename, date_part = default_name.rsplit(".", 1)
        base, ext = original_csv_filename.rsplit(".", 1)

        # 絶対パス
        return f"{base}-{date_part}.{ext}"


class GPTLogRecordJsonTimedRotatingFileHandler(BaseGPTLogRecordTimedRotatingFileHandler):
    """GPTLogRecord を JSON で出力するための TimedRotatingFileHandler"""


class GPTLogRecordCSVTimedRotatingFileHandler(BaseGPTLogRecordTimedRotatingFileHandler):
    """GPTLogRecord を CSV で出力するための TimedRotatingFileHandler

    ファイルに書き出し後、ヘッダーを追加する
    """

    headers = [
        "timestamp",
        "doc_retrieval_type",
        "rag_qa",
        "rag_knowledge",
        "metadata",
        "question",
        "response",
        "latency",
    ]

    def custom_rotator(self, source: str, dest: str) -> None:
        """files_to_upload/ 以下にファイルを移動しつつ、ローテーションを行う"""
        self._add_header_to_csv(file_path=pathlib.Path(source))
        super().custom_rotator(source, dest)

    def _add_header_to_csv(self, *, file_path: pathlib.Path) -> None:
        """CSV ファイルにヘッダーを追加する(with BOM)"""
        bom = "\ufeff"

        header_line = bom + ",".join(self.headers) + "\n"

        if file_path.exists():
            with file_path.open("r") as file:
                content = file.read()

            with file_path.open("w") as file:
                file.seek(0)
                file.write(header_line + content)


def _gpt_log_record_factory(name, *args, **kwargs):
    """特定の logger の場合のみ GPTLogRecord を使う"""
    if name in ["interaction_logger"]:
        return GPTLogRecord(name, *args, **kwargs)
    else:
        return logging.LogRecord(name, *args, **kwargs)


def setup_logger() -> None:
    """ロガーの設定"""
    _setup_structlog()
    _setup_stdlib_handlers()


def _setup_structlog():
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.render_to_log_kwargs,
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _setup_stdlib_handlers():
    log_level = logging.INFO

    # root
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            keep_exc_info=True,
            keep_stack_info=True,
        ),
    )
    logging.root.setLevel(log_level)
    logging.root.handlers = [handler]

    # 対話ログ部分
    interaction_logger = logging.getLogger("interaction_logger")
    interaction_logger.setLevel(log_level)

    # JSON ハンドラの設定
    json_handler = GPTLogRecordJsonTimedRotatingFileHandler("log/interaction_log.json", when="H", interval=1, backupCount=24 * 14)
    json_handler.setLevel(log_level)
    json_handler.setFormatter(JsonFormatter())
    interaction_logger.addHandler(json_handler)

    # CSV ハンドラの設定
    csv_handler = GPTLogRecordCSVTimedRotatingFileHandler("log/interaction_log.csv", when="H", interval=1, backupCount=24 * 14)
    csv_handler.setLevel(log_level)
    csv_handler.setFormatter(CsvFormatter())
    interaction_logger.addHandler(csv_handler)

    logging.setLogRecordFactory(_gpt_log_record_factory)
