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

# -----------------------------
# Step 2: Add SKUs & merge into an EXISTING promo (promo/bonus fixed)
# -----------------------------

import json as _json  # avoid name shadowing if you've imported json above

def _normalize_skus(raw: str):
    """Accept comma/newline separated SKUs, strip quotes/spaces, dedupe (order preserved)."""
    if not raw:
        return []
    parts = raw.replace("\r", "").replace("\n", ",").split(",")
    cleaned, seen = [], set()
    for p in parts:
        s = p.strip().strip('"').replace(" ", "")
        if s and s not in seen:
            cleaned.append(s)
            seen.add(s)
    return cleaned

def _ensure_promos_dict(data: dict):
    """Return {promo_key: {'products':[...], 'bonus': '...'}} from parsed JSON."""
    promos = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                products = v.get("products", []) or []
                bonus = v.get("bonus", "")
                promos[str(k)] = {
                    "products": [str(x) for x in products if str(x).strip()],
                    "bonus": str(bonus) if bonus is not None else ""
                }
    return promos

def _rows_from_promos(promos: dict):
    rows = []
    for promo_key, payload in promos.items():
        bonus = payload.get("bonus", "")
        for sku in payload.get("products", []):
            rows.append({
                "promo_num": promo_key,
                "product_sku": sku,
                "bonus": bonus
            })
    return rows

st.subheader("2) Add SKUs to an existing promo")

# Require JSON from Step 1
current_json = st.session_state.get("current_json", {})
if not isinstance(current_json, dict) or not current_json:
    st.warning("Paste valid promo JSON in step 1 first. No promos found.")
else:
    promos_dict = _ensure_promos_dict(current_json)
    existing_promos = sorted(promos_dict.keys())

    # Promo selection (existing only)
    target_promo = st.selectbox(
        "Select promo (existing only)",
        existing_promos,
        index=0 if existing_promos else None,
        placeholder="Choose a promo"
    )

    # Show fixed bonus for the selected promo (read-only)
    fixed_bonus = promos_dict.get(target_promo, {}).get("bonus", "")
    st.text_input("Bonus (fixed from JSON)", value=fixed_bonus, disabled=True)

    # SKU input (comma or newline)
    sku_text = st.text_area(
        "Paste SKUs to add (comma or newline separated; quotes/spaces OK)",
        height=140,
        placeholder='225805, 225807\n225808'
    )
    new_skus = _normalize_skus(sku_text)

    colb1, colb2 = st.columns([1, 1])

    def _merge_into_existing(promos: dict, promo_key: str, skus: list):
        """Merge SKUs into an existing promo. Bonus stays unchanged. No new promos allowed.
        Returns (promos or None, added_count, skipped_dupes_list)."""
    if promo_key not in promos:
        return None, 0, ["Selected promo no longer exists. Reload JSON."]
    promos = {k: {"products": list(v.get("products", [])), "bonus": v.get("bonus", "")}
              for k, v in promos.items()}
    seen = set(promos[promo_key]["products"])
    added = 0
    skipped = []
    for s in skus:
        if s in seen:
            skipped.append(s)        # collect duplicates for feedback
        else:
            promos[promo_key]["products"].append(s)
            seen.add(s)
            added += 1
    return promos, added, skipped

    with colb1:
    if st.button("Preview merge", use_container_width=True):
        if not target_promo:
            st.warning("Select an existing promo.")
        elif not new_skus:
            st.warning("Paste at least one SKU to merge.")
        else:
            preview_promos, added_cnt, skipped = _merge_into_existing(promos_dict, target_promo, new_skus)
            if preview_promos is None:
                st.error("Selected promo no longer exists. Reload JSON.")
            else:
                rows = _rows_from_promos(preview_promos)
                df_prev = pd.DataFrame(rows, columns=["promo_num", "product_sku", "bonus"])
                st.success(f"Preview: will add {added_cnt} SKU(s) to '{target_promo}'. Total rows after: {len(df_prev)}.")
                if skipped:
                    st.info(f"Skipped (already present): {', '.join(skipped)}")
                st.dataframe(df_prev, use_container_width=True)
                st.code(_json.dumps(preview_promos, indent=2), language="json")

with colb2:
    if st.button("Apply merge", type="primary", use_container_width=True):
        if not target_promo:
            st.warning("Select an existing promo.")
        elif not new_skus:
            st.warning("Paste at least one SKU to merge.")
        else:
            merged_promos, added_cnt, skipped = _merge_into_existing(promos_dict, target_promo, new_skus)
            if merged_promos is None:
                st.error("Selected promo no longer exists. Reload JSON.")
            else:
                # Persist merged JSON
                st.session_state["current_json"] = merged_promos
                merged_rows = _rows_from_promos(merged_promos)
                df_merged = pd.DataFrame(merged_rows, columns=["promo_num", "product_sku", "bonus"])
                st.success(f"Merged {added_cnt} SKU(s) into '{target_promo}'. Total rows now: {len(df_merged)}.")
                if skipped:
                    st.info(f"Skipped (already present): {', '.join(skipped)}")
                st.dataframe(df_merged, use_container_width=True)
                st.code(_json.dumps(merged_promos, indent=2), language="json")

                # Exports (JSON / CSV / TXT)
                st.subheader("Exports")

                # JSON
                json_bytes = _json.dumps(merged_promos, indent=2).encode("utf-8")
                st.download_button(
                    "Download updated JSON",
                    data=json_bytes,
                    file_name="promos_updated.json",
                    mime="application/json"
                )

                # CSV
                csv_bytes = df_merged.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download CSV (promo_num, product_sku, bonus)",
                    data=csv_bytes,
                    file_name="promo_table.csv",
                    mime="text/csv"
                )

                # TXT: "SKU", per line with CRLF
                txt_lines = "\r\n".join([f"\"{sku}\"," for sku in df_merged["product_sku"].tolist()])
                st.download_button(
                    "Download TXT (\"SKU\", per line)",
                    data=txt_lines.encode("utf-8"),
                    file_name="skus.txt",
                    mime="text/plain"
                )