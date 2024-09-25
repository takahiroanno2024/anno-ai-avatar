import requests
from utils import measure_time


@measure_time
def request_to_voice(text: str, version: str, base_endpoint: str = "http://127.0.0.1:7200") -> bytes | None:
    """テキストを音声に変換する"""
    url = f"{base_endpoint}/voice/{version}"
    params = {"text": text, "model_id": 0}
    response = requests.post(url, params=params, timeout=50)
    if response.status_code == 200:
        return response.content

    return None


@measure_time
def request_to_reply(text: str, base_endpoint: str = "http://127.0.0.1:7200") -> str | None:
    """AITuber に問い合わせて返答を取得する"""
    url = f"{base_endpoint}/reply"
    params = {
        "inputtext": text,
    }

    response = requests.post(url, data=params, timeout=20)
    if response.status_code == 200:
        return response.json()

    return None


def request_to_embedding(text: str, base_endpoint: str = "http://127.0.0.1:7200") -> str | None:
    """AITuber に問い合わせて返答を取得する"""
    url = f"{base_endpoint}/get_info"
    params = {
        "query": text,
        "top_k": 3,
    }

    response = requests.get(url, params=params, timeout=20)
    if response.status_code == 200:
        return response.json()

    return None


@measure_time
def request_to_hallucination(text: str, base_endpoint: str = "http://127.0.0.1:7200") -> str | None:
    """AITuber に問い合わせて返答を取得する"""
    url = f"{base_endpoint}/hallucination"
    params = {
        "text": text,
    }

    response = requests.post(url, json=params, timeout=20)
    if response.status_code == 200:
        return response.json()

    return None
