import json
from collections.abc import AsyncIterator

import jaconv
from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from janome.tokenizer import Tokenizer

from src.azure_speech_synthesizer import AzureSpeechSynthesizer, add_wav_header
from src.config import settings

client = AsyncElevenLabs(
    api_key=settings.ELEVENLABS_API_KEY,
)


class TextToSpeech:
    """TextToSpeech を行うクラス

    いくつか手法があるが、このクラスにまとめておく
    """

    def __init__(self):
        self._client = AsyncElevenLabs(
            api_key=settings.ELEVENLABS_API_KEY,
        )

        self._sample_rate = 44100
        # 学習済みモデルのID(あんのボイス)
        self._elevenlabs_voice_id = "tyMlTSDYc5JhCakLJuAX"

    @property
    def output_format(self) -> str:
        """音声出力フォーマット

        pcm_44100: 44100HzのPCMデータをデフォで使用する
        """
        return f"pcm_{self._sample_rate}"

    async def text_to_speech_stream(self, text: str) -> bytes:
        """入力テキストを音声(WAV)に変換する"""
        text = self._convert_kanji_to_hiragana(text)
        stream = client.text_to_speech.convert_as_stream(
            voice_id=self._elevenlabs_voice_id,
            output_format=self.output_format,
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.7,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
            ),
        )

        return await self._stream_to_bytes(stream)

    async def text_to_speech_with_azure_tts(self, text: str) -> bytes:
        """入力テキストを Azure TTS -> AsyncElevenLabs STSで音声(WAV)に変換する"""
        speech_synthesizer = AzureSpeechSynthesizer()
        tts_data = speech_synthesizer.speech_synthesis_to_audio_data_stream(text)
        tts_data = add_wav_header(tts_data)

        stream = client.speech_to_speech.convert_as_stream(
            voice_id=self._elevenlabs_voice_id,
            audio=tts_data,
            output_format=self.output_format,
            model_id="eleven_multilingual_sts_v2",
            voice_settings=json.dumps(
                {
                    "stability": 0.9,
                    "similarity_boost": 1.0,
                    "style": 0.0,
                    "use_speaker_boost": True,
                }
            ),
        )

        return await self._stream_to_bytes(stream)

    async def azure_text_to_speech(self, text: str, voice_name="ja-JP-NanamiNeural", rate="+10%") -> bytes:
        """入力テキストを Azure TTSで音声(WAV)に変換する"""
        speech_synthesizer = AzureSpeechSynthesizer(voice_name=voice_name, rate=rate)
        tts_data = speech_synthesizer.speech_synthesis_to_audio_data_stream(text)
        tts_data = add_wav_header(tts_data)
        return tts_data

    async def _stream_to_bytes(self, stream: AsyncIterator[bytes]) -> bytes:
        """ストリームをバイト列(WAV)に変換する"""
        audio_data = []
        async for chunk in stream:
            audio_data.append(chunk)

        return add_wav_header(b"".join(audio_data))

    def _convert_kanji_to_hiragana(self, text):
        """テキストをひらがなに変換する"""
        t = Tokenizer()
        tokens = t.tokenize(text)
        result = ""
        for token in tokens:
            surface = token.surface
            reading = token.reading
            if reading == "*":
                # 記号や数字等の読みが取得できない場合はsurfaceをそのまま使う
                result += surface
            elif reading == jaconv.kata2hira(surface):
                result += surface
            elif reading == jaconv.hira2kata(surface):
                result += surface
            else:
                result += jaconv.kata2hira(reading)
        return result
