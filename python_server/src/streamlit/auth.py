import pathlib

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def _load_authenticator() -> stauth.Authenticate:
    """認証情報を読み込む"""
    config_path = pathlib.Path(__file__).parent / "auth.yml"
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(config["credentials"], config["cookie"]["name"], config["cookie"]["key"], config["cookie"]["expiry_days"], config["pre-authorized"])
    return authenticator


def auth() -> None:
    """認証を行う"""
    authenticator = _load_authenticator()
    _, is_authenticated, _ = authenticator.login()

    if is_authenticated is None:
        st.error("ログイン情報を入力して下さい")
        st.stop()
    elif not is_authenticated:
        st.error("正しいログイン情報を入力して下さい")
        st.stop()
    elif is_authenticated:
        st.write("ログインしました")
        st.experimental_rerun()


def is_authenticated() -> bool:
    """認証状態を返す"""
    return True
    return st.session_state.get("authentication_status", False)


def logout_component() -> None:
    """ログアウトボタンを表示する"""
    if is_authenticated():
        authenticator = _load_authenticator()
        authenticator.logout()
