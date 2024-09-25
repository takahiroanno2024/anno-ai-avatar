import click
import structlog

from src.config import settings
from src.google_drive import GoogleDrive
from src.logger import setup_logger

slogger = structlog.get_logger(__name__)

setup_logger()


@click.command()
def main() -> None:
    """ローテートしたログをGoogle Driveにアップロードする

    log/files_to_upload/... 以下にあるファイルをGoogle Driveにアップロードする

    アップロードが完了したら、ファイルを削除する
    ファイルは1時間おきに生成されるので、定期的に実行することを想定している。
    """
    google_drive = GoogleDrive()

    csv_files_to_upload = list(settings.PYTHON_SERVER_ROOT.glob("log/files_to_upload/*csv"))
    json_files_to_upload = list(settings.PYTHON_SERVER_ROOT.glob("log/files_to_upload/*json"))

    # 本番環境では AITuber > Logs > Raw
    folder_id = settings.GOOGLE_DRIVE_FOLDER_ID

    for file_path in csv_files_to_upload:
        google_drive.upload(file_path=file_path, folder_id=folder_id, mime_type="text/csv")
        file_path.unlink()

    for file_path in json_files_to_upload:
        google_drive.upload(file_path=file_path, folder_id=folder_id, mime_type="application/json")
        file_path.unlink()


if __name__ == "__main__":
    main()
