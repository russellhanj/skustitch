import os
import streamlit as st

# --- App settings ---
APP_NAME = "SKUStitch"
PASS = os.environ.get("APP_PASS") or "Russ0707"  # <-- change "Russ0707" to your secret

# --- Simple passphrase gate ---
with st.sidebar:
    entered = st.text_input("Passphrase", type="password")
if entered != PASS:
    st.title(APP_NAME)
    st.info("Enter the passphrase in the sidebar to continue.")
    st.stop()

# --- Rest of your app code starts here ---
st.title(APP_NAME)
st.caption("Internal tool for updating Cushion Inserts promo JSON & SKUs.")

# ... paste the rest of the Streamlit app code from earlier ...
