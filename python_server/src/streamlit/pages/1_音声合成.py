import io

import streamlit as st
from api_client import request_to_voice
from auth import auth, is_authenticated


def main() -> None:
    """音声合成ページの表示"""
    if not is_authenticated():
        auth()
        return

    st.markdown("""こちらのページでは、音声合成を試すことができます。
音声合成は以下の2つのバージョンがあります。
* v1: ElevenLabsのみを利用
* v2: Microsoft AzureのText to Speechを使った後、ElevenLabsで音声変換を実施
""")
    text = st.text_area("生成させる音声を入力して下さい", "")
    tts_version = st.selectbox("音声合成方式のバージョンを選択して下さい", ["v1", "v2"]) or "v2"
    if not st.button("音声生成"):
        return

    replaced_version = tts_version.replace("v1", "")
    with st.spinner("音声生成中"):
        audio_bytes, response_time = request_to_voice(text, replaced_version)
        if audio_bytes is None:
            st.error("エラーが発生しました")
            return
        audio_stream = io.BytesIO(audio_bytes)
        st.write(f"合成時間: {response_time:.2f} sec")
        st.audio(audio_stream, format="audio/wav")


if __name__ == "__main__":
    main()
