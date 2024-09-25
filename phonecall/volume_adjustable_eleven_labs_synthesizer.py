from typing import Type
from vocode.streaming.models.synthesizer import (
    ElevenLabsSynthesizerConfig,
)
from vocode.streaming.synthesizer.abstract_factory import AbstractSynthesizerFactory
from vocode.streaming.synthesizer.azure_synthesizer import AzureSynthesizer
from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer
from vocode.streaming.synthesizer.cartesia_synthesizer import CartesiaSynthesizer
from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer
from vocode.streaming.synthesizer.eleven_labs_websocket_synthesizer import ElevenLabsWSSynthesizer
from vocode.streaming.synthesizer.play_ht_synthesizer import PlayHtSynthesizer
from vocode.streaming.synthesizer.play_ht_synthesizer_v2 import PlayHtSynthesizerV2
from vocode.streaming.synthesizer.rime_synthesizer import RimeSynthesizer
from vocode.streaming.synthesizer.stream_elements_synthesizer import StreamElementsSynthesizer

from pydantic.v1 import validator

import asyncio
import hashlib
from typing import Optional

from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from loguru import logger

from vocode.streaming.models.audio import AudioEncoding, SamplingRate
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer, SynthesisResult
from vocode.streaming.utils.create_task import asyncio_create_task_with_done_error_log

import numpy as np
import audioop

ELEVEN_LABS_ADAM_VOICE_ID = "pNInz6obpgDQGcFmaJgB"
ELEVEN_LABS_BASE_URL = "https://api.elevenlabs.io/v1/"
STREAMED_CHUNK_SIZE = 16000 * 2 // 4  # 1/8 of a second of 16kHz audio with 16-bit samples

class VolumeAdjustableElevenLabsSynthesizerConfig(ElevenLabsSynthesizerConfig, type="random"):  # type: ignore
    volume_factor: float = 1.0

class VolumeAdjustableElevenLabsSynthesizerFactory(AbstractSynthesizerFactory):
    def create_synthesizer(
        self,
        synthesizer_config: VolumeAdjustableElevenLabsSynthesizerConfig,
    ):
        return VolumeAdjustableElevenLabsSynthesizer(synthesizer_config)

class VolumeAdjustableElevenLabsSynthesizer(ElevenLabsSynthesizer):
    def adjust_volume(self, chunk: bytes, factor: float = 1) -> bytes:
        # チャンクを線形PCMデータにデコードする（エンコーディング形式に基づく）
        if self.synthesizer_config.audio_encoding == AudioEncoding.MULAW:
            # μ-lawエンコードされたデータを線形PCMに変換
            chunk = audioop.ulaw2lin(chunk, 2)
        
        # チャンクをnumpy配列に変換
        audio_array = np.frombuffer(chunk, dtype=np.int16)
        
        # 音量を調整し、クリッピング処理を行う
        adjusted_audio_array = np.clip(audio_array * factor, -32768, 32767).astype(np.int16)
        
        # 調整後のデータをバイト配列に戻す
        adjusted_bytes = adjusted_audio_array.tobytes()
        
        # 必要に応じて、元のエンコーディング形式にエンコードする
        if self.synthesizer_config.audio_encoding == AudioEncoding.MULAW:
            # 線形PCMデータをμ-lawに再エンコード
            return audioop.lin2ulaw(adjusted_bytes, 2)
        else:
            # その他の場合は、変更されたPCMデータを直接返す
            return adjusted_bytes

    async def get_chunks(
        self,
        url: str,
        headers: dict,
        body: dict,
        chunk_size: int,
        chunk_queue: asyncio.Queue[Optional[bytes]],
    ):
        try:
            async_client = self.async_requestor.get_client()
            stream = await async_client.send(
                async_client.build_request(
                    "POST",
                    url,
                    headers=headers,
                    json=body,
                ),
                stream=True,
            )

            if not stream.is_success:
                error = await stream.aread()
                logger.error(f"ElevenLabs API failed: {stream.status_code} {error.decode('utf-8')}")
                raise Exception(f"ElevenLabs API returned {stream.status_code} status code")
            async for chunk in stream.aiter_bytes(chunk_size):
                if self.upsample:
                    chunk = self._resample_chunk(
                        chunk,
                        self.sample_rate,
                        self.upsample,
                    )
                chunk = self.adjust_volume(chunk, self.synthesizer_config.volume_factor)
                chunk_queue.put_nowait(chunk)
        except asyncio.CancelledError:
            pass
        finally:
            chunk_queue.put_nowait(None)  # treated as sentinel
