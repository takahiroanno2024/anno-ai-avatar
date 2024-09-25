import pathlib
from typing import Literal

import structlog
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import settings

slogger = structlog.get_logger(__name__)


class GoogleDrive:
    """Google Drive API"""

    def __init__(self) -> None:
        credentials = service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS, scopes=["https://www.googleapis.com/auth/drive.file"])

        self._service = build("drive", "v3", credentials=credentials)

    def upload(
        self,
        *,
        file_path: pathlib.Path,
        folder_id: str,
        mime_type: Literal["text/csv"] | Literal["application/json"],
    ) -> None:
        """Google Driveにファイルをアップロードする

        Args:
            file_path: アップロードするファイルのパス
            mime_type: ファイルのMIMEタイプ
        """
        media = MediaFileUpload(file_path, mimetype=mime_type)

        file_metadata = {
            "name": file_path.name,
            "parents": [folder_id],
        }

        file = self._service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        slogger.info(f"Uploaded {file_path}", file_id=file.get("id"), file_path=file_path)
