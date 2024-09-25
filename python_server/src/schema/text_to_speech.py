from pydantic import BaseModel


class TTSRequest(BaseModel):
    """Text to speech のリクエスト"""

    text: str
    model_id: str
