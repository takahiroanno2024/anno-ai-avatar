import logging
import os

import gspread
import streamlit as st
from api_client import request_to_reply
from auth import auth, is_authenticated
from google.oauth2.service_account import Credentials

LOGGER = logging.getLogger(__name__)


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
    credential_path = "gcp_credentials.json"
    sheet_url = "https://docs.google.com/spreadsheets/d/1b9h3gHoteP5las5ZadAkgMeQSDyot-8WUidwCsF5uR4/edit?gid=0#gid=0"
    try:
        worksheet = _load_sheet(credential_path, sheet_url)
    except FileNotFoundError:
        LOGGER.warning("Google Sheetsの認証情報が見つかりませんでした")
        worksheet = None

    st.markdown("""こちらのページでは、入力した内容に対してテキストでAITuberの返答を生成します""")
    text = st.text_area("質問を入力して下さい", "")

    if not st.button("質問を送信") and st.session_state.get("previous_text") is None:
        return

    if not text == st.session_state.get("previous_text"):
        with st.spinner("返答を生成中"):
            reply_json, reply_time = request_to_reply(text)
            LOGGER.debug("reply_json: %s", reply_json)
            reply = reply_json["response_text"]
            image_filename = reply_json["image_filename"]
            st.write(f"**返答生成にかかった時間: {reply_time:.2f} sec**")
            st.session_state["reply"] = reply
            st.session_state["image_filename"] = image_filename
            if reply is None:
                st.error("エラーが発生しました")
                return

    st.markdown("### 返答テキスト")
    reply = st.session_state["reply"]
    st.write(reply)

    st.markdown("### 返答するスライドの番号")
    st.write("スライドの内容は手元にマニフェストデックを用意して確認下さい。")
    st.write(image_filename)

    st.session_state["previous_text"] = text

    if worksheet:
        with st.form("feedback_form"):
            st.markdown("### 返答テキストのフィードバック")

            st.markdown("""返答のクオリティを評価してください。
    * OK: 返答に問題がない場合に選択して下さい。
    * どちらとも言えない: クオリティが高くはないが、炎上リスクはない場合に選択して下さい。
    * NG: 返答に問題がある。炎上するリスクや法律的に問題がある場合、重大な嘘が含まれている場合に選択して下さい。
    """)
            feedback = st.selectbox("返答の品質", ["OK", "どちらとも言えない", "NG"])
            comments = st.text_area("NG・どちらとも言えないの場合、具体的な理由を教えてください")

            if st.form_submit_button("フィードバックを送信"):
                if feedback:
                    # Append feedback to the Google Sheet
                    worksheet.append_row([text, reply, feedback, comments])
                    st.success("フィードバックを送信しました")
                else:
                    st.error("フィードバックを選択してください")


if __name__ == "__main__":
    DEBUG = os.environ.get("DEBUG", "false").lower() not in ["false", "no", "0"]

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)7s from %(name)s in %(pathname)s:%(lineno)d: " "%(message)s",
        level=logging.DEBUG if DEBUG else logging.INFO,
        force=True,
    )
    main()
