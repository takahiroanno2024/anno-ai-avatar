import gspread
import streamlit as st
from api_client import request_to_embedding, request_to_reply
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

    if not st.button("質問を送信"):
        return

    with st.spinner("返答を生成中"):
        reply, reply_time = request_to_reply(text)
        embedding_data = request_to_embedding(text)
        st.write(f"**返答生成にかかった時間: {reply_time:.2f} sec**")
        st.write("## 返答テキスト")
        st.write(reply["response_text"])
        st.write("## RAGで用いたデータ")
        st.write(embedding_data)


if __name__ == "__main__":
    main()
