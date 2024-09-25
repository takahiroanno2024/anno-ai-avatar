import streamlit as st
from auth import auth, is_authenticated, logout_component

if not is_authenticated():
    auth()
    st.stop()

logout_component()
