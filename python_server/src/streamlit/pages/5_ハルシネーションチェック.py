import gspread
import streamlit as st
from api_client import request_to_hallucination
from auth import auth, is_authenticated
from google.oauth2.service_account import Credentials


def _load_client(credential_path: str) -> gspread.Client:
    """Google Sheetsのクライアントを返す"""
    credentials = Credentials.from_service_account_file(credential_path, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    gc = gspread.authorize(credentials)
    return gc


def _load_sheet(credential_path: str, sheet_url: str) -> gspread.Worksheet:
    """Google Sheetsのワークシートを返す"""
    gc = _load_client(credential_path)
    spreadsheet = gc.open_by_url(sheet_url)
    worksheet = spreadsheet.sheet1

    return worksheet


def main():
    """音声対話ページの表示"""
    if not is_authenticated():
        auth()
        return

    st.markdown("""こちらのページでは、入力した内容に対してテキストでAITuberの返答を生成します""")
    text = st.text_area("質問を入力して下さい", "")

    if not st.button("質問を送信") and st.session_state.get("previous_text") is None:
        return

    if not text == st.session_state.get("previous_text"):
        with st.spinner("返答を生成中"):
            reply_json, reply_time = request_to_hallucination(text)
            reply = reply_json["response_text"]
            # image_filename = reply_json["image_filename"]
            st.write(f"**返答生成にかかった時間: {reply_time:.2f} sec**")
            st.session_state["reply"] = reply
            # st.session_state["image_filename"] = image_filename
            if reply is None:
                st.error("エラーが発生しました")
                return

    st.markdown("### 返答テキスト")
    st.write(reply_json)


if __name__ == "__main__":
    main()
