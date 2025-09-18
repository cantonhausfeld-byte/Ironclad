import streamlit as st

from ironclad.app.Picks import render as render_picks

st.set_page_config(page_title="Ironclad Control Center", layout="wide")

render_picks()
