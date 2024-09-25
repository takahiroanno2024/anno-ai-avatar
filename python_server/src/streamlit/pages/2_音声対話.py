import io

import streamlit as st
from api_client import request_to_reply, request_to_voice
from auth import auth, is_authenticated


def main() -> None:
    """音声対話ページの表示"""
    if not is_authenticated():
        auth()
        return

    st.markdown("""こちらのページでは、入力した内容に対して音声でAITuberの返答を生成します""")
    text = st.text_area("質問を入力して下さい", "")
    tts_version = st.selectbox("音声合成方式のバージョンを選択して下さい", ["v1", "v2"]) or "v2"

    if not st.button("質問を送信"):
        return

    with st.spinner("返答を生成中"):
        reply, reply_time = request_to_reply(text)

    if reply is None:
        st.error("エラーが発生しました")
        return

    st.markdown("### 返答テキスト")
    st.write(reply)

    converted_reply = reply.replace("安野", "庵野")
    st.markdown("### 返答音声")
    with st.spinner("音声生成中"):
        replaced_version = tts_version.replace("v1", "")
        audio_bytes, voice_time = request_to_voice(converted_reply, replaced_version)
        if audio_bytes is None:
            st.error("エラーが発生しました")
            return

        audio_stream = io.BytesIO(audio_bytes)
        st.write(f"返答テキスト生成にかかった時間: {reply_time:.2f} sec")
        st.write(f"音声生成にかかった時間時間: {voice_time:.2f} sec")
        st.audio(audio_stream, format="audio/wav")


if __name__ == "__main__":
    main()
