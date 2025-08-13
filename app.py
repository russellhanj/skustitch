import os
import streamlit as st
import json
import pandas as pd

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

# --- Step 1: Paste JSON and display table ---
st.subheader("1) Paste existing promo JSON")

with st.expander("Sample JSON format", expanded=False):
    st.code(
        '''{
  "promo1": { "products": ["218948","218950"], "bonus": "130009" },
  "promo2": { "products": ["218960","218961"], "bonus": "130011" }
}''',
        language="json"
    )

json_text = st.text_area("Promo JSON", height=220, placeholder='{"promo1": {"products": ["218948","218950"], "bonus": "130009"}}')

if json_text.strip():
    try:
        data = json.loads(json_text)

        # Build rows: one row per SKU with promo & bonus
        rows = []
        if isinstance(data, dict):
            for promo_key, payload in data.items():
                if isinstance(payload, dict):
                    products = payload.get("products", [])
                    bonus = payload.get("bonus", "")
                    if isinstance(products, list):
                        for sku in products:
                            if str(sku).strip():
                                rows.append({
                                    "promo_num": str(promo_key),
                                    "product_sku": str(sku).strip(),
                                    "bonus": str(bonus)
                                })

        if rows:
            df = pd.DataFrame(rows, columns=["promo_num", "product_sku", "bonus"])
            st.success(f"Parsed {len(df)} rows across {df['promo_num'].nunique()} promos.")
            st.dataframe(df, use_container_width=True)

            # Keep for later steps (adding SKUs, exports)
            st.session_state["current_json"] = data
            st.session_state["current_df"] = df
        else:
            st.warning("No products found. Ensure structure like: {\"promoX\": {\"products\": [\"SKU1\",\"SKU2\"], \"bonus\": \"...\"}}")

    except json.JSONDecodeError as e:
        st.error(f"JSON error: {e.msg} (line {e.lineno}, column {e.colno})")
else:
    st.info("Paste your promo JSON above to see it as a table.")

