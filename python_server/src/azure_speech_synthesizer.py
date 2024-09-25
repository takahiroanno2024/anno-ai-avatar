import struct

import azure.cognitiveservices.speech as speechsdk

from src.config import settings


class AzureSpeechSynthesizer:
    """Azureの音声合成をストリームに保存するためのクラス"""

    def __init__(self, voice_name="ja-JP-KeitaNeural", pitch: str = "+10%", rate: str = "-5%") -> None:
        self.speech_config = speechsdk.SpeechConfig(subscription=settings.AZURE_SPEECH_KEY, region="japaneast")
        self.speech_config.speech_synthesis_voice_name = voice_name
        self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Raw44100Hz16BitMonoPcm)
        self.voice_name = voice_name
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
        self.pitch = pitch
        self.rate = rate

    def speech_synthesis_to_audio_data_stream(self, text: str) -> bytes | None:
        """音声合成した結果をwavのバイト列として返す"""
        ssml_text = self._create_ssml(text, self.pitch, self.rate)

        # SSMLを使用して音声合成を行う
        result = self.speech_synthesizer.speak_ssml_async(ssml_text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data_stream = speechsdk.AudioDataStream(result)
            audio_data_stream.position = 0

            audio_chunks = []
            while True:
                audio_buffer = bytes(4096)  # Create a byte buffer of size 4096
                filled_size = audio_data_stream.read_data(audio_buffer)
                if filled_size == 0:
                    break
                audio_chunks.append(audio_buffer[:filled_size])

            audio_data = b"".join(audio_chunks)

            if self._is_valid_audio(audio_data):
                return audio_data

            print("Error: Audio data is empty or invalid.")
            return None

        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
            return None

    def _create_ssml(self, text: str, pitch: str, rate: str) -> str:
        """SSMLを生成する"""
        ssml_template = """
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ja-JP">
            <voice name="{}">
                <prosody pitch="{}" rate="{}">
                    {}
                </prosody>
            </voice>
        </speak>
        """
        return ssml_template.format(self.voice_name, pitch, rate, text)

    @classmethod
    def _is_valid_audio(cls, audio_data):
        if audio_data.strip(b"\x00"):
            return True
        return False


def add_wav_header(audio_data, *, sample_rate=44100) -> bytes:
    """Adds a WAV header to the given audio data."""
    num_channels = 1  # Mono
    sample_width = 2  # 2 bytes per sample
    byte_rate = sample_rate * num_channels * sample_width
    block_align = num_channels * sample_width
    subchunk2_size = len(audio_data)
    chunk_size = 36 + subchunk2_size

    wav_header = struct.pack("<4sI4s4sIHHIIHH4sI", b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1, num_channels, sample_rate, byte_rate, block_align, sample_width * 8, b"data", subchunk2_size)

    return wav_header + audio_data
