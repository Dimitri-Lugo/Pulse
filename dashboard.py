import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
import os
import io
import math
import html as html_mod
from datetime import datetime
from PIL import Image
import db_ops
import market_data
import llm_utils


# Dialog for editing quantities or removing holdings from the portfolio
@st.dialog("Manage Portfolio")
def pulse_manage_portfolio_dialog(email: str):
    _mgr_rows = db_ops.get_watchlist(email)
    if not _mgr_rows:
        st.markdown('<p style="color:#5a3a7a;font-size:0.78rem;font-family:monospace;text-align:center;padding:0.6rem 0;">No assets in your portfolio yet.</p>', unsafe_allow_html=True)
        return
    _mgr_prices = [market_data.get_current_price(r["ticker"]) for r in _mgr_rows]

    # Toggling "Select all" forces the editor to re-initialize with fresh values
    _sel_all = st.checkbox("Select all", key="pf_mgr_sel_all")
    _mgr_df_orig = pd.DataFrame({
        "Remove": [_sel_all] * len(_mgr_rows),
        "Ticker": [r["ticker"] for r in _mgr_rows],
        "Quantity": [r["amount"] for r in _mgr_rows],
        "Current Price": [float(p) if p else 0.0 for p in _mgr_prices],
    })
    _mgr_df_edited = st.data_editor(
        _mgr_df_orig,
        column_config={
            "Remove": st.column_config.CheckboxColumn("", width="small"),
            "Ticker": st.column_config.TextColumn("Ticker", required=True),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, format="%.6g"),
            "Current Price": st.column_config.NumberColumn("Current Price", disabled=True, format="$%.2f"),
        },
        disabled=["Current Price"],
        num_rows="fixed",
        hide_index=True,
        use_container_width=True,
        key=f"pf_mgr_editor_{_sel_all}",
    )
    _to_remove = _mgr_df_edited[_mgr_df_edited["Remove"] == True]
    if not _to_remove.empty:
        _n = len(_to_remove)
        _label = f"Remove {_n} Asset{'s' if _n > 1 else ''}"
        if st.button(_label, type="primary", use_container_width=True, key="pf_mgr_delete"):
            _keep = _mgr_df_edited[_mgr_df_edited["Remove"] != True]
            _new_entries = []
            for _, _row in _keep.iterrows():
                _tk = str(_row.get("Ticker", "") or "").upper().strip()
                try:
                    _am = float(_row.get("Quantity", 0) or 0)
                except (ValueError, TypeError):
                    _am = 0.0
                if _tk and _am > 0:
                    _new_entries.append({"ticker": _tk, "amount": _am})
            db_ops.set_watchlist(email, _new_entries)
            st.rerun()
    if st.button("Save Changes", type="primary", use_container_width=True, key="pf_mgr_save"):
        _new_entries = []
        for _, _erow in _mgr_df_edited.iterrows():
            _etk = str(_erow.get("Ticker", "") or "").upper().strip()
            try:
                _eam = float(_erow.get("Quantity", 0) or 0)
            except (ValueError, TypeError):
                _eam = 0.0
            if _etk and _eam > 0:
                _new_entries.append({"ticker": _etk, "amount": _eam})
        db_ops.set_watchlist(email, _new_entries)
        st.rerun()


# Dialog for viewing account info, uploading a profile picture, or logging out
@st.dialog("Account")
def pulse_profile_dialog():
    un = st.session_state.get("username", "user@pulse.com")
    _role = st.session_state.get("role", "User")
    _pic_bytes = st.session_state.get("profile_pic", None)

    # Shows the current avatar centered at the top of the dialog
    if _pic_bytes:
        _pic_b64 = base64.b64encode(_pic_bytes).decode()
        st.markdown(
            f'<div style="display:flex;justify-content:center;margin-bottom:10px;">'
            f'<img src="data:image/png;base64,{_pic_b64}" '
            f'style="width:64px;height:64px;border-radius:50%;object-fit:cover;'
            f'border:2px solid #B026FF;"/></div>',
            unsafe_allow_html=True,
        )
    else:
        _dname = st.session_state.get("nickname", "") or un.split("@")[0]
        _initials_dlg = "".join([w[0].upper() for w in _dname.split()[:2]])[:2] or _dname[:1].upper()
        st.markdown(
            f'<div style="display:flex;justify-content:center;margin-bottom:10px;">'
            f'<div style="width:64px;height:64px;border-radius:50%;'
            f'background:linear-gradient(135deg,#B026FF,#55007a);'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:1.2rem;font-weight:700;color:#fff;">{_initials_dlg}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<p style="text-align:center;color:#B026FF;font-size:0.88rem;font-weight:600;margin:0 0 6px;font-family:monospace;word-break:break-all;">{html_mod.escape(un)}</p>'
        f'<p style="text-align:center;color:#7a5a9a;font-size:0.72rem;margin:0 0 12px;font-family:monospace;">{html_mod.escape(_role)}</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<p style="color:#7a5a9a;font-size:0.65rem;font-family:monospace;margin:0 0 4px;letter-spacing:0.08em;">PROFILE PICTURE</p>', unsafe_allow_html=True)
    _uploaded = st.file_uploader("Choose file", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed", key="profile_pic_upload")
    if _uploaded is not None:
        # Only processes if this is a new file that hasn't been saved yet
        _file_id = f"{_uploaded.name}_{_uploaded.size}"
        if _file_id != st.session_state.get("_last_pic_upload_id"):
            try:
                _img = Image.open(_uploaded).convert("RGBA")
                _w, _h = _img.size
                _side = min(_w, _h)
                _left = (_w - _side) // 2
                _top = (_h - _side) // 2
                _img = _img.crop((_left, _top, _left + _side, _top + _side))
                _img = _img.resize((256, 256), Image.LANCZOS)
                _mask = Image.new("L", (256, 256), 0)
                from PIL import ImageDraw
                ImageDraw.Draw(_mask).ellipse((0, 0, 256, 256), fill=255)
                _result = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                _result.paste(_img, mask=_mask)
                _buf = io.BytesIO()
                _result.save(_buf, format="PNG")
                _png_bytes = _buf.getvalue()
                db_ops.set_profile_pic(un, _png_bytes)
                st.session_state["profile_pic"] = _png_bytes
                st.session_state["_last_pic_upload_id"] = _file_id
                st.toast("Profile picture updated!")
                st.rerun()
            except Exception as _e:
                st.toast(f"Upload failed: {_e}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Log out", type="primary", use_container_width=True, key="pulse_dlg_logout"):
        _tok = st.session_state.pop("_auth_token", None)
        if _tok:
            db_ops.delete_auth_token(_tok)
        st.session_state["authenticated"] = False
        st.session_state["current_page"] = "login"
        st.session_state["_pending_cookie_delete"] = True
        st.session_state.pop("portfolio", None)
        st.rerun()


# Dialog that opens when the HIGH CORRELATION alert is clicked
# Calls the Groq LLM to generate specific diversification advice based on the current portfolio
@st.dialog("Correlation Risk Details")
def pulse_risk_details_dialog(correlation_index: float, top_holdings: tuple):
    st.markdown(
        f'<p style="color:#B026FF;font-size:0.82rem;font-family:monospace;margin:0 0 6px;">'
        f'Correlation Index: <strong>{correlation_index:.2f}</strong> &nbsp;'
        f'<span style="color:#FF007F;font-size:0.72rem;">(threshold: 0.70)</span></p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#7a5a9a;font-size:0.72rem;font-family:monospace;margin:0 0 4px;">'
        'Top holdings driving correlation:</p>',
        unsafe_allow_html=True,
    )
    for _tk, _al in top_holdings:
        st.markdown(
            f'<p style="color:#B026FF;font-size:0.70rem;font-family:monospace;margin:0 0 2px;">'
            f'&nbsp;&nbsp;• {_tk}: {_al:.1f}%</p>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<hr style="border:none;border-top:1px solid #2a1545;margin:10px 0 8px;">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#7a5a9a;font-size:0.72rem;font-family:monospace;margin:0 0 6px;">'
        'AI Diversification Recommendations:</p>',
        unsafe_allow_html=True,
    )
    with st.spinner("Generating advice…"):
        _groq_key = st.secrets.get("GROQ_API_KEY", "")
        _advice = llm_utils.get_diversification_advice(_groq_key, correlation_index, top_holdings)
    st.markdown(
        f'<p style="color:#d0c0e8;font-size:0.75rem;font-family:monospace;line-height:1.6;'
        f'white-space:pre-wrap;">{html_mod.escape(_advice)}</p>',
        unsafe_allow_html=True,
    )


# Main dashboard — wrapped in a fragment so it reruns every 60 seconds to refresh prices
# I chose to use a fragment here so the data updates without a full page reload interrupting the user
@st.fragment(run_every=60)
def render_dashboard():
    # Loads the logo and strips its black background so it renders cleanly on the dark dashboard
    _logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logo.png")
    if os.path.exists(_logo_path):
        img = Image.open(_logo_path).convert("RGBA")
        px = img.getdata()
        img.putdata([(0, 0, 0, 0) if (r < 40 and g < 40 and b < 40) else (r, g, b, a) for r, g, b, a in px])
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        _b64 = base64.b64encode(buf.getvalue()).decode()
        _logo_core = f'<img src="data:image/png;base64,{_b64}" width="50" height="50" style="display:block;position:relative;z-index:1;border-radius:10px;">'
    else:
        _logo_core = '<div style="width:50px;height:50px;background:linear-gradient(135deg,#9D00FF,#5a0099);border-radius:10px;position:relative;z-index:1;"></div>'
    _logo_img = f'<div style="position:relative;display:inline-flex;align-items:center;justify-content:center;"><div class="logo-pulse-aura"></div>{_logo_core}</div>'
    st.markdown("""<style>
    @keyframes logo-aura-pulse{0%,100%{transform:scale(0.8);opacity:0.5;}50%{transform:scale(1.8);opacity:1;}}
    @keyframes pulse-text-glow{0%,100%{text-shadow:0 0 10px rgba(176,38,255,0.7),0 0 22px rgba(176,38,255,0.35);}50%{text-shadow:0 0 26px rgba(176,38,255,1),0 0 58px rgba(176,38,255,0.95),0 0 110px rgba(176,38,255,0.5);}}
    .logo-pulse-aura{position:absolute;width:60px;height:60px;border-radius:50%;background:radial-gradient(circle,rgba(157,0,255,0.9) 0%,rgba(157,0,255,0.45) 40%,transparent 70%);animation:logo-aura-pulse 3s ease-in-out infinite;z-index:0;}
    .pulse-text-animate{animation:pulse-text-glow 3s ease-in-out infinite;}
    [data-testid="stHeader"]{display:none!important;}
    html,body{overflow:auto!important;height:auto!important;min-height:100vh!important;margin:0!important;padding:0!important;background:#000000!important;}
    .stApp,[data-testid="stAppViewContainer"]{overflow:auto!important;background:#000000!important;height:auto!important;min-height:100vh!important;}
    .stApp section.main,.stApp [data-testid="stMain"]{overflow:auto!important;background:#000000!important;max-width:100vw!important;width:100%!important;padding:0!important;flex:1!important;}
    .stApp [data-testid="stMainBlockContainer"],.stApp [class*="block-container"]{max-width:100%!important;width:100%!important;}
    html body .stApp div[data-testid="block-container"],html body .stApp [data-testid="stMainBlockContainer"]{position:relative!important;top:auto!important;left:auto!important;transform:none!important;max-width:100%!important;width:100%!important;padding:0.55rem 1.3rem 72px!important;border:none!important;border-radius:0!important;margin:0!important;background:transparent!important;z-index:auto!important;animation:none!important;box-shadow:none!important;}
    html body .stApp div[data-testid="block-container"]>div,html body .stApp [data-testid="stMainBlockContainer"]>div{padding:0!important;max-width:100%!important;}
    [data-testid="stVerticalBlockBorderWrapper"]{border:1px solid rgba(157,0,255,0.6)!important;border-radius:10px!important;background:#03000a!important;box-shadow:0 0 10px rgba(157,0,255,0.14)!important;}
    [data-testid="stVerticalBlockBorderWrapper"]>div{background:#03000a!important;}
    .dh{color:#B026FF;font-size:0.65rem;font-weight:700;letter-spacing:0.16em;margin:0 0 0.5rem;font-family:monospace;text-transform:uppercase;white-space:nowrap;text-align:left;}
    .dh-center{color:#B026FF;font-size:0.65rem;font-weight:700;letter-spacing:0.16em;margin:0 0 0.5rem;font-family:monospace;text-transform:uppercase;text-align:center;white-space:nowrap;}
    .stApp [data-testid="stTextInput"]{min-height:0!important;}
    .stApp [data-testid="stTextInput"]>div{min-height:0!important;height:auto!important;}
    .stApp [data-testid="stTextInput"]>div>div{min-height:0!important;height:auto!important;padding:0!important;}
    .stApp [data-testid="stTextInput"] [data-baseweb="input"]{min-height:0!important;height:auto!important;}
    .stApp [data-testid="stTextInput"] [data-baseweb="base-input"]{min-height:0!important;height:auto!important;padding:0!important;}
    .stApp [data-testid="stTextInput"] input{background:#070010!important;color:#ddc8ff!important;border:1px solid #3a0075!important;border-radius:5px!important;font-size:0.76rem!important;font-family:monospace!important;padding:0.1rem 0.5rem!important;height:auto!important;min-height:0!important;line-height:1.2!important;}
    .stApp [data-testid="stTextInput"] input:focus{border-color:#B026FF!important;box-shadow:0 0 7px rgba(176,38,255,0.4)!important;}
    .stApp [data-testid="stTextInput"] label{display:none!important;}
    html body .stApp [data-testid="stButton"]{width:100%!important;display:block!important;}
    html body .stApp button[data-testid="stBaseButton-primary"],html body .stApp [data-testid="stBaseButton-primary"]{background-color:#070010!important;background:#070010!important;border:1px solid #B026FF!important;font-family:monospace!important;letter-spacing:0.08em!important;font-size:0.72rem!important;font-weight:600!important;padding:0!important;border-radius:5px!important;min-height:0!important;height:1.3rem!important;line-height:1.3rem!important;width:100%!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:none!important;color:#B026FF!important;}
    html body .stApp button[data-testid="stBaseButton-primary"]:hover,html body .stApp [data-testid="stBaseButton-primary"]:hover{background-color:#0d0020!important;background:#0d0020!important;border-color:#d966ff!important;color:#d966ff!important;box-shadow:0 0 7px rgba(176,38,255,0.4)!important;}
    html body .stApp button[data-testid="stBaseButton-primary"]>div,html body .stApp button[data-testid="stBaseButton-primary"] p{padding:0!important;margin:0!important;line-height:1!important;color:#B026FF!important;font-weight:600!important;font-family:monospace!important;letter-spacing:0.08em!important;}
    html body .stApp [data-testid="stBaseButton-primary"] *{color:#B026FF!important;font-weight:600!important;}
    .stElementToolbar,[data-testid="StyledFullScreenButton"],[data-testid="stBaseButton-headerNoPadding"]{display:none!important;}
    [data-testid="stDataFrame"] thead th{background:#080018!important;color:#B026FF!important;font-size:0.59rem!important;font-family:monospace!important;letter-spacing:0.1em!important;border-bottom:1px solid rgba(157,0,255,0.4)!important;}
    [data-testid="stDataFrame"] tbody td{color:#c8a8e8!important;font-size:0.72rem!important;background:#03000a!important;font-family:monospace!important;}
    [data-testid="stDataFrame"] tbody tr:hover td{background:#0a0020!important;}
    [class*="st-key-pulse_portfolio_card"] [data-testid="stDataFrame"] [class*="resize"],[class*="st-key-pulse_portfolio_card"] [data-testid="stDataFrame"] [class*="dvn-resize"]{display:none!important;pointer-events:none!important;}
    [class*="st-key-pulse_portfolio_card"] [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"]{pointer-events:none!important;}
    [class*="st-key-pulse_portfolio_card"] [data-testid="stDataFrame"] *{cursor:default!important;}
    [data-testid="stSegmentedControl"]{gap:0!important;}
    [data-testid="stSegmentedControl"] label{background:transparent!important;color:#3d2260!important;border:1px solid #1e0035!important;border-radius:4px!important;font-size:0.62rem!important;font-family:monospace!important;letter-spacing:0.06em!important;padding:3px 9px!important;transition:all 0.15s!important;}
    [data-testid="stSegmentedControl"] label:has(input:checked){background:#18003a!important;color:#B026FF!important;border-color:#B026FF!important;box-shadow:0 0 10px rgba(176,38,255,0.35)!important;}
    [data-testid="stToggle"] span[data-testid="stWidgetLabel"]{display:none!important;}
    [data-testid="stToggle"]>div>div{background-color:#B026FF!important;}
    div[data-testid="stHorizontalBlock"]{align-items:stretch!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]{display:flex!important;flex-direction:column!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div[data-testid="stVerticalBlock"]{flex:1!important;display:flex!important;flex-direction:column!important;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_portfolio_card"]) div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]),div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]){flex-wrap:nowrap!important;align-items:center!important;justify-content:flex-start!important;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_portfolio_card"]) div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"])>div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"],div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"])>div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"]{flex:0 1 auto!important;justify-content:center!important;min-height:0!important;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_portfolio_card"]) div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] [data-testid="stTextInput"],div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] [data-testid="stTextInput"]{width:7.25rem!important;max-width:7.25rem!important;min-width:0!important;box-sizing:border-box!important;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_portfolio_card"]) div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] [data-testid="stTextInput"]>div,div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_portfolio_card"]) div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] [data-testid="stTextInput"] [data-baseweb="input"],div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] [data-testid="stTextInput"]>div,div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] [data-testid="stTextInput"] [data-baseweb="input"]{max-width:100%!important;width:100%!important;box-sizing:border-box!important;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_portfolio_card"]) div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] button[data-testid="stBaseButton-primary"],div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"]:has(>div[data-testid="stColumn"]:nth-child(3) button[data-testid="stBaseButton-primary"]) div[data-testid="stVerticalBlock"] button[data-testid="stBaseButton-primary"]{width:auto!important;min-width:4.25rem!important;display:inline-flex!important;}
    div[data-testid="stColumn"]:not(:last-child) div[data-testid="stVerticalBlockBorderWrapper"]{flex:1!important;display:flex!important;flex-direction:column!important;min-height:0!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:first-child{flex:0 0 auto!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:last-child{flex:1!important;display:flex!important;flex-direction:column!important;min-height:440px!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"]{min-height:560px!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"]){align-items:stretch!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:nth-child(2){display:flex!important;flex-direction:column!important;align-self:stretch!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:nth-child(2)>div{flex:1!important;display:flex!important;flex-direction:column!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:nth-child(2)>div>div[data-testid="stVerticalBlockBorderWrapper"]{flex:1!important;display:flex!important;flex-direction:column!important;min-height:614px!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:nth-child(2)>div>div[data-testid="stVerticalBlockBorderWrapper"]>div{flex:1!important;display:flex!important;flex-direction:column!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:first-child{display:flex!important;flex-direction:column!important;align-self:stretch!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:first-child>div{flex:1!important;display:flex!important;flex-direction:column!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:first-child>div>div[data-testid="stVerticalBlockBorderWrapper"]{flex:1!important;display:flex!important;flex-direction:column!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:last-child>div{background:#03000a!important;flex:1!important;display:flex!important;flex-direction:column!important;min-height:0!important;}
    div[data-testid="stHorizontalBlock"]:has([data-testid="stDataFrame"])>div[data-testid="stColumn"]:last-child>div[data-testid="stVerticalBlock"]{min-height:560px!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:last-child div[data-testid="stVerticalBlock"]{gap:0!important;flex:1 1 0!important;min-height:0!important;justify-content:flex-start!important;}
    [class*="st-key-pulse_volatility"]{min-height:424px!important;display:flex!important;flex-direction:column!important;}
    [data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_volatility"]){min-height:434px!important;display:flex!important;flex-direction:column!important;}
    [data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-pulse_volatility"]) *{user-select:none!important;-webkit-user-select:none!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:last-child [data-testid="stMarkdownContainer"]{width:100%!important;display:block!important;text-align:center!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:last-child>div[data-testid="stVerticalBlock"],section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:last-child>div>div[data-testid="stVerticalBlock"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:last-child>div[data-testid="stVerticalBlock"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:last-child>div>div[data-testid="stVerticalBlock"]{padding-top:0!important;margin-top:0!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:first-child > div{padding-bottom:0!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:first-child [data-testid="stMarkdownContainer"]{overflow:visible!important;}
    .dh-center{color:#B026FF;font-size:0.65rem;font-weight:700;letter-spacing:0.16em;margin:0 0 0.5rem;font-family:monospace;text-transform:uppercase;text-align:center!important;width:100%!important;display:block!important;white-space:nowrap;}
    [data-testid="stVerticalBlock"]>[style*="flex-direction: column;"]>[data-testid="stVerticalBlock"]{gap:0.5rem!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child>div[data-testid="stVerticalBlock"]>[style*="flex-direction: column;"]>[data-testid="stVerticalBlock"]{gap:0.28rem!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type,[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type{align-items:center!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) [data-testid="stVerticalBlock"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) [data-testid="stVerticalBlock"]{min-height:44px!important;align-items:center!important;justify-content:flex-end!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]{display:flex!important;flex-direction:row!important;align-items:center!important;justify-content:flex-end!important;gap:6px!important;width:100%!important;flex-wrap:nowrap!important;background:transparent!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:first-child,[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:first-child{flex:0 0 auto!important;width:auto!important;min-width:0!important;max-width:42px!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:nth-child(2),[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:nth-child(2){flex:0 1 auto!important;min-width:0!important;width:auto!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:nth-child(2)>div[data-testid="stVerticalBlock"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:nth-child(2)>div[data-testid="stVerticalBlock"]{align-items:center!important;justify-content:center!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:nth-child(2) [data-testid="stElementContainer"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:nth-child(2) [data-testid="stElementContainer"]{width:auto!important;max-width:100%!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:first-child>div[data-testid="stVerticalBlock"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:first-child>div[data-testid="stVerticalBlock"]{flex:0 0 auto!important;justify-content:center!important;align-items:center!important;min-height:0!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"]{display:flex!important;align-items:center!important;margin:0!important;padding:0!important;line-height:0!important;transform:translateY(-3px)!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"] p,[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) div[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"] p{margin:0!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) button[kind="secondary"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) button[kind="secondary"]{background:#06000f!important;color:#B026FF!important;border:1px solid rgba(157,0,255,0.45)!important;border-radius:8px!important;height:34px!important;min-height:34px!important;padding:0 14px!important;width:auto!important;max-width:min(240px,100%)!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;font-family:monospace!important;font-size:0.68rem!important;font-weight:600!important;letter-spacing:0.03em!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) button[kind="secondary"]:hover,[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) button[kind="secondary"]:hover{background:#08001a!important;border-color:#B026FF!important;color:#d966ff!important;box-shadow:0 0 10px rgba(176,38,255,0.22)!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) button[kind="secondary"] p,[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) button[kind="secondary"] p{margin:0!important;line-height:1.2!important;color:inherit!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;max-width:200px!important;}
    section.main [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) [data-testid="stButton"],[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type>div[data-testid="stColumn"]:nth-child(3) [data-testid="stButton"]{width:auto!important;min-width:0!important;}
    div[data-testid="stDialog"] [data-testid="stBaseButton-primary"]{background:#0a0015!important;border:1px solid rgba(157,0,255,0.5)!important;color:#B026FF!important;font-family:monospace!important;font-size:0.72rem!important;letter-spacing:0.08em!important;border-radius:6px!important;height:auto!important;min-height:0!important;padding:10px 14px!important;width:100%!important;}
    div[data-testid="stDialog"] [data-testid="stBaseButton-primary"]:hover{background:#150025!important;border-color:#B026FF!important;color:#d966ff!important;}
    [data-testid="stForm"]{border:none!important;padding:0!important;background:transparent!important;margin:0!important;}
    [data-testid="stFormSubmitButton"]{display:none!important;height:0!important;overflow:hidden!important;pointer-events:none!important;}
    /* ── Portfolio card edit-toggle header ─────────────────────────── */
    /* The header [9,1] columns must not flex-stretch to fill the 560 px card.
       We override only the first stElementContainer's descendants (the header
       row), leaving the form columns ([1.1,1.1,0.62]) and the dataframe
       completely untouched. */
    [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stHorizontalBlock"]{flex:0 0 auto!important;min-height:0!important;height:auto!important;align-items:center!important;}
    [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stColumn"]{flex:0 0 auto!important;min-height:0!important;height:auto!important;}
    [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stVerticalBlock"]{flex:0 0 auto!important;min-height:0!important;height:auto!important;}
    /* The pencil edit-toggle button: no box, no border, rotated colour emoji */
    html body .stApp [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stColumn"]:last-child button{background:transparent!important;border:none!important;box-shadow:none!important;font-size:0.85rem!important;padding:0 2px!important;min-height:0!important;height:auto!important;width:auto!important;line-height:1!important;font-weight:400!important;letter-spacing:0!important;display:inline-flex!important;align-items:center!important;justify-content:flex-end!important;}
    html body .stApp [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stColumn"]:last-child button:hover{background:rgba(157,0,255,0.08)!important;border-radius:3px!important;}
    /* Rotate the inner content div so the pencil tilts naturally */
    html body .stApp [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stColumn"]:last-child button>div{transform:rotate(-45deg)!important;display:inline-block!important;transition:transform 0.25s ease!important;}
    html body .stApp [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stColumn"]:last-child button:hover>div{transform:rotate(-35deg)!important;}
    html body .stApp [class*="st-key-pulse_portfolio_card"]>[data-testid="stElementContainer"]:first-child [data-testid="stColumn"]:last-child button p{font-size:inherit!important;padding:0!important;margin:0!important;line-height:1!important;}
    </style>""", unsafe_allow_html=True)
    _uname = st.session_state.get("username", "user@pulse.com")
    _nickname = st.session_state.get("nickname", "").strip()
    # Falls back to the email prefix if the user hasn't set a nickname yet
    if _nickname:
        _dname = _nickname
    else:
        _dname = _uname.split("@")[0].replace(".", " ").replace("_", " ").title()
    _initials = "".join([w[0].upper() for w in _dname.split()[:2]])[:2] or _dname[:1].upper()
    _disp = _dname[:12] + ".." if len(_dname) > 12 else _dname
    # Header row — PULSE title on the left, logo in the center, profile button on the right
    hc1, hc2, hc3 = st.columns([1, 1, 1])
    with hc1:
        st.markdown('<p class="pulse-text-animate" style="color:#B026FF;font-size:2rem;font-weight:900;letter-spacing:0.28em;margin:0;padding:0.2rem 0;font-family:monospace;">PULSE</p>', unsafe_allow_html=True)
    with hc2:
        st.markdown(f'<div style="display:flex;justify-content:center;align-items:center;padding:0.2rem 0;"><div style="padding:10px;background:transparent;">{_logo_img}</div></div>', unsafe_allow_html=True)
    with hc3:
        _av_col, _btn_col = st.columns([1, 5], gap="small")
        with _av_col:
            _pic_bytes_hdr = st.session_state.get("profile_pic", None)
            if _pic_bytes_hdr:
                _pic_b64_hdr = base64.b64encode(_pic_bytes_hdr).decode()
                _av_html = (
                    f'<img src="data:image/png;base64,{_pic_b64_hdr}" '
                    f'style="width:32px;height:32px;border-radius:50%;object-fit:cover;'
                    f'border:1.5px solid #B026FF;transform:translateY(3px);flex-shrink:0;"/>'
                )
            else:
                _av_html = (
                    f'<div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#B026FF,#55007a);'
                    f'display:flex;align-items:center;justify-content:center;font-size:0.62rem;font-weight:700;color:#fff;'
                    f'letter-spacing:0.03em;flex-shrink:0;transform:translateY(3px);">{_initials}</div>'
                )
            st.markdown(
                f'<div style="display:flex;justify-content:flex-end;align-items:center;width:100%;height:34px;min-height:34px;">'
                f'{_av_html}</div>',
                unsafe_allow_html=True,
            )
        with _btn_col:
            _trigger = f"{_disp}  \u25bc"
            if st.button(_trigger, key="pulse_profile_open", type="secondary"):
                pulse_profile_dialog()
    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(157,0,255,0.5) 30%,rgba(157,0,255,0.5) 70%,transparent);margin:0.1rem 0 0.6rem;"></div>', unsafe_allow_html=True)
    # Three-column layout — portfolio on the left, analytics in the center, risk feed on the right
    col_l, col_c, col_r = st.columns([1, 2, 1], gap="medium")
    with col_l:
        with st.container(border=True, key="pulse_portfolio_card"):
            _pf_email = st.session_state.get("username", "")
            # Header row: PORTFOLIO label on the left, pencil icon to open the manage dialog on the right
            _pf_h1, _pf_h2 = st.columns([9, 1])
            with _pf_h1:
                st.markdown('<p class="dh">PORTFOLIO</p>', unsafe_allow_html=True)
            with _pf_h2:
                if st.button("✏️", key="pf_edit_toggle", use_container_width=True):
                    pulse_manage_portfolio_dialog(_pf_email)
            # Clears the input fields after a successful ADD — must happen before the widgets render
            if st.session_state.pop("_clear_pf_inputs", False):
                st.session_state["pt"] = ""
                st.session_state["pa"] = ""
            with st.form(key="pf_form", clear_on_submit=False, border=False):
                pf_c1, pf_c2, pf_c3 = st.columns([1.1, 1.1, 0.62], gap="small", vertical_alignment="center")
                with pf_c1:
                    t_in = st.text_input("tk", "", placeholder="Ticker", key="pt", label_visibility="collapsed")
                with pf_c2:
                    a_in = st.text_input("am", "", placeholder="Shares/Tokens", key="pa", label_visibility="collapsed")
                with pf_c3:
                    submitted = st.form_submit_button("ADD", use_container_width=False, type="primary")
            if submitted and t_in and a_in:
                try:
                    amt = float(a_in.replace(",", ""))
                    tk = t_in.upper().strip()
                    if amt <= 0:
                        # Negative quantities are allowed to reduce a position, as long as the user has enough shares
                        _existing = next((r for r in db_ops.get_watchlist(_pf_email) if r["ticker"] == tk), None)
                        if _existing is None:
                            st.toast("Quantity must be greater than 0 for a new position.", icon="⚠️")
                        elif _existing["amount"] + amt < 0:
                            st.toast(f"Would reduce {tk} below 0 (current quantity: {_existing['amount']:g}).", icon="⚠️")
                        else:
                            db_ops.upsert_watchlist(_pf_email, tk, amt)
                            st.session_state["_clear_pf_inputs"] = True
                            st.rerun()
                    elif not market_data.validate_ticker(tk):
                        st.toast(f'"{tk}" is not a valid ticker symbol.', icon="⚠️")
                    else:
                        db_ops.upsert_watchlist(_pf_email, tk, amt)
                        st.session_state["_clear_pf_inputs"] = True
                        st.rerun()
                except ValueError:
                    st.toast("Please enter a valid quantity.", icon="⚠️")
            # Loads the portfolio from the database and calculates market-value-based exposure for each holding
            # I chose to fetch all prices in a single batch call instead of one per ticker for speed
            _pf_rows = db_ops.get_watchlist(_pf_email)
            _pf_qtys = []
            _pf_prices_f = []
            _pf_mkt_vals = []
            _total_mkt_val = 0.0
            if _pf_rows:
                _pf_qtys = [r["amount"] for r in _pf_rows]
                _batch = market_data.get_batch_prices(tuple(r["ticker"] for r in _pf_rows))
                _raw_prices = [_batch.get(r["ticker"]) for r in _pf_rows]
                _pf_prices_f = [float(p) if p else 0.0 for p in _raw_prices]
                # Market value = quantity × price, Exposure = each holding's market value / total portfolio value
                _pf_mkt_vals = [q * p for q, p in zip(_pf_qtys, _pf_prices_f)]
                _total_mkt_val = sum(_pf_mkt_vals)
                _pf_dict = {
                    "Ticker": [r["ticker"] for r in _pf_rows],
                    "Price": _pf_prices_f,
                    "Quantity": [float(q) for q in _pf_qtys],
                    "Exposure": [
                        round(mv / _total_mkt_val * 100, 1) if _total_mkt_val > 0 else 0.0
                        for mv in _pf_mkt_vals
                    ],
                }
            else:
                _pf_dict = {"Ticker": [], "Price": [], "Quantity": [], "Exposure": []}
            df_p = pd.DataFrame(_pf_dict).sort_values("Exposure", ascending=False).reset_index(drop=True)
            st.dataframe(df_p, column_config={
                "Ticker": st.column_config.TextColumn("Asset", width="small"),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
                "Quantity": st.column_config.NumberColumn("Quantity", format="%.6g", width="small"),
                "Exposure": st.column_config.NumberColumn("Exposure", format="%.1f%%", width="small"),
            }, hide_index=True, use_container_width=True, height=460)
    with col_c:
        with st.container(border=True):
            _now_str = datetime.now().strftime("%b %d, %Y  %I:%M %p")
            _ah1, _ah2 = st.columns([1, 1])
            with _ah1:
                st.markdown('<p class="dh">ANALYTICS</p>', unsafe_allow_html=True)
            with _ah2:
                st.markdown(
                    f'<p style="text-align:right;font-family:monospace;font-size:0.58rem;'
                    f'color:#B026FF;letter-spacing:0.06em;margin:0;padding-top:0.35rem;">'
                    f'LAST UPDATED<br>'
                    f'<span style="color:#B026FF;font-size:0.64rem;">{_now_str}</span></p>',
                    unsafe_allow_html=True,
                )
            timeframe = st.segmented_control("TF", ["7 Days", "30 Days", "90 Days", "1 Year"], default="30 Days", key="tf", label_visibility="collapsed")
            n = {"7 Days": 7, "30 Days": 30, "90 Days": 90, "1 Year": 365}.get(timeframe or "30 Days", 30)

            # Weights each ticker by its share of the total portfolio market value for the correlation calculation
            _c_tickers, _c_weights_raw = [], []
            if _pf_rows and _total_mkt_val > 0:
                _c_tickers = [r["ticker"] for r in _pf_rows]
                _c_weights_raw = [mv / _total_mkt_val for mv in _pf_mkt_vals]

            _corr_series = None
            if len(_c_tickers) >= 2:
                _corr_series = market_data.get_weighted_correlation_series(
                    tuple(_c_tickers), tuple(_c_weights_raw)
                )

            # Slices the series to the last n trading days so the timeframe selector works correctly
            if _corr_series is not None and not _corr_series.empty:
                # iloc[-n:] gives exactly the last n trading days — safely returns all rows if fewer than n exist
                _plot = _corr_series.iloc[-n:]
                corr = np.clip(_plot.values.astype(float), -1.0, 1.0)
                # Full date strings keep each trading day unique on the x-axis
                x_labels = _plot.index.strftime("%b %d '%y" if n >= 90 else "%b %d").tolist()
                _step = max(1, len(x_labels) // 6)
                tick_vals = x_labels[::_step]
                # For longer views, shows a cleaner "Mon 'YY" format on the tick labels
                tick_text = [_plot.index[i].strftime("%b '%y") for i in range(0, len(x_labels), _step)] if n >= 90 else tick_vals
            else:
                # Flat neutral line as a fallback when there are fewer than 2 tickers or not enough history
                corr = np.full(n, 0.0)
                if n <= 30:
                    x_labels = [f"Day {i+1}" for i in range(n)]
                else:
                    _fb_dates = pd.date_range(end=pd.Timestamp.today(), periods=n, freq="B")
                    x_labels = _fb_dates.strftime("%b %d '%y" if n >= 90 else "%b %d").tolist()
                tick_vals = x_labels[::max(1, len(x_labels) // 6)]
                tick_text = tick_vals
            st.markdown('<p style="color:#B026FF;font-size:0.78rem;letter-spacing:0.13em;font-family:monospace;margin:0.2rem 0 0.1rem;padding-left:17rem;">RISK CORRELATION GRAPH</p>', unsafe_allow_html=True)
            fig_c = go.Figure()
            fig_c.add_trace(go.Scatter(x=x_labels, y=corr, mode="lines", line=dict(color="#B026FF", width=2.8, shape="spline"), fill="tozeroy", fillcolor="rgba(176,38,255,0.06)"))
            fig_c.update_layout(
                paper_bgcolor="#000000", plot_bgcolor="#030008",
                font=dict(color="#B026FF", family="monospace", size=11),
                margin=dict(l=44, r=12, t=8, b=52),
                xaxis=dict(gridcolor="#0d001c", zeroline=False, tickfont=dict(size=10, color="#B026FF"), tickvals=tick_vals, ticktext=tick_text, title=dict(text="")),
                yaxis=dict(gridcolor="#0d001c", zeroline=True, zerolinecolor="#2a1545", zerolinewidth=1, range=[-1.0, 1.12], tickvals=[-1.0, -0.5, 0.0, 0.5, 0.7, 1.0], ticktext=["-1.0", "-0.5", "0.0", "0.5", "0.7", "1.0"], tickfont=dict(size=10, color="#B026FF"), title=dict(text="Correlation Index", font=dict(size=12, color="#B026FF"))),
                showlegend=False, height=451, dragmode=False,
                shapes=[dict(type="line", x0=x_labels[0], x1=x_labels[-1], y0=0.7, y1=0.7, line=dict(color="#FF007F", width=1.2, dash="dot"))],
                annotations=[dict(text="Time", x=0.47, y=-0.13, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="#B026FF", family="monospace"))],
            )
            st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False}, key="pulse_corr_chart")
    with col_r:
        with st.container(border=True, key="pulse_risk_feed"):
            _rf_hdr = go.Figure()
            _rf_hdr.add_annotation(text="RISK ALERT FEED", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, xanchor="center", yanchor="middle", font=dict(color="#B026FF", size=18, family="monospace"))
            _rf_hdr.update_layout(paper_bgcolor="#000000", height=30, margin=dict(t=0, b=0, l=0, r=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(_rf_hdr, use_container_width=True, config={"displayModeBar": False, "staticPlot": True}, key="pulse_rf_hdr")
            # Compares the most recent correlation value against the 0.70 threshold to decide which alert to show
            _CORR_THRESHOLD = 0.70
            _latest_corr = float(corr[-1]) if corr is not None and len(corr) > 0 else 0.0

            _WRAP_STYLE = (
                '<style>'
                '.alert-feed-wrap{width:100%;padding:0;box-sizing:border-box;}'
                '#pulse-high-card{transform:translate(-38px,-26px);}'
                '[class*="st-key-btn_rf_high"]{transform:translate(-38px,-26px);}'
                '</style>'
            )

            if _latest_corr < _CORR_THRESHOLD:
                st.markdown(
                    _WRAP_STYLE
                    + '<style>'
                    + '[class*="st-key-pulse_diversified_card"]{'
                    + 'transform:translate(0px,-30px)!important;}'
                    + '[class*="st-key-pulse_diversified_card"]>div{'
                    + 'border:1px solid #3d2458;border-radius:6px;'
                    + 'padding:5px 10px 0px;min-height:24px;width:100%;box-sizing:border-box;'
                    + 'display:flex;align-items:center;}'
                    + '</style>',
                    unsafe_allow_html=True,
                )
                with st.container(key="pulse_diversified_card"):
                    st.markdown(
                        '<span style="color:#39ff14;font-size:0.68rem;font-family:monospace;">&#10003;</span>'
                        '<span style="color:#B026FF;font-size:0.68rem;font-family:monospace;"> Your portfolio is sufficiently diversified.</span>',
                        unsafe_allow_html=True,
                    )
            else:
                # Grabs the top 5 holdings by exposure to use in the alert label and pass to the LLM
                _top_holdings = tuple()
                if not df_p.empty:
                    _th = df_p[["Ticker", "Exposure"]].head(5)
                    _top_holdings = tuple(
                        zip(_th["Ticker"].tolist(), _th["Exposure"].tolist())
                    )

                _high_pair = (
                    "/".join(h[0] for h in _top_holdings[:2])
                    if len(_top_holdings) >= 2 else "Portfolio"
                )

                st.markdown(_WRAP_STYLE, unsafe_allow_html=True)
                if st.button(
                    f"HIGH CORRELATION ALERT: {_high_pair}\n\nJust now · Critical threshold exceeded",
                    key="btn_rf_high",
                    use_container_width=True,
                ):
                    pulse_risk_details_dialog(_latest_corr, _top_holdings)
        with st.container(border=True, key="pulse_volatility"):
            _hdr = go.Figure()
            _hdr.add_annotation(text="VOLATILITY GAUGES", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, xanchor="center", yanchor="middle", font=dict(color="#B026FF", size=16, family="monospace"))
            _hdr.update_layout(paper_bgcolor="#000000", height=26, margin=dict(t=0, b=0, l=0, r=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(_hdr, use_container_width=True, config={"displayModeBar": False, "staticPlot": True}, key="pulse_vol_hdr")

            # Builds a semicircle volatility gauge with a custom needle overlay
            def _gauge(val, title, subtext):
                # Maps each 10-point band to a color from deep purple → red to show rising risk
                _gradient = ["#280060","#3d0090","#5500aa","#6e00b8","#820099","#960075","#aa0050","#c00030","#d80015","#f00005"]
                _steps = []
                for _i in range(10):
                    _lo, _hi = _i * 10, (_i + 1) * 10
                    if val >= _hi:
                        _steps.append({"range": [_lo, _hi], "color": _gradient[_i]})
                    elif val > _lo:
                        _steps.append({"range": [_lo, val], "color": _gradient[_i]})
                        _steps.append({"range": [val, _hi], "color": "#0a0018"})
                    else:
                        _steps.append({"range": [_lo, _hi], "color": "#0a0018"})
                _c = _gradient[min(int(val // 10), 9)]

                # Needle geometry — (x=0, y=0) is the gauge pivot at the bottom center of the arc
                # scaleanchor="y" keeps the pixel scale equal so the angle stays geometrically accurate
                _ang = math.radians(180.0 - (val / 100.0) * 180.0)
                _perp = _ang + math.pi / 2.0
                _nr = 0.88   # Needle tip radius — calibrated to reach the outer gauge arc
                _bw = 0.033  # Half-width of the needle base
                _nx = [_bw * math.cos(_perp), _nr * math.cos(_ang), -_bw * math.cos(_perp), _bw * math.cos(_perp)]
                _ny = [_bw * math.sin(_perp), _nr * math.sin(_ang), -_bw * math.sin(_perp), _bw * math.sin(_perp)]

                fig = go.Figure()
                fig.add_trace(go.Indicator(
                    mode="gauge", value=val,
                    domain={"x": [0, 1], "y": [0.13, 0.87]},
                    gauge={
                        "axis": {
                            "range": [0, 100],
                            "tickvals": [0, 50, 100],
                            "ticktext": ["LOW", "", "HIGH"],
                            "tickfont": {"color": "#B026FF", "size": 12, "family": "monospace"},
                            "tickwidth": 0,
                            "tickcolor": "rgba(0,0,0,0)",
                        },
                        "bar": {"color": "rgba(0,0,0,0)", "thickness": 0.3},
                        "bgcolor": "#000000", "borderwidth": 0,
                        "steps": _steps,
                        "threshold": {"line": {"color": "#ffffff", "width": 4}, "thickness": 0.88, "value": val},
                    },
                ))
                # Needle drawn as a filled triangle pointing from the pivot hub to the arc
                fig.add_trace(go.Scatter(
                    x=_nx, y=_ny, fill="toself",
                    fillcolor="rgba(255,255,255,0.88)",
                    line=dict(color="rgba(0,0,0,0)", width=0),
                    mode="lines", showlegend=False, hoverinfo="skip",
                    xaxis="x", yaxis="y",
                ))
                # Small white circle at the pivot center so the needle looks properly anchored
                fig.add_trace(go.Scatter(
                    x=[0], y=[0], mode="markers",
                    marker=dict(color="white", size=6, symbol="circle"),
                    showlegend=False, hoverinfo="skip",
                    xaxis="x", yaxis="y",
                ))
                fig.update_layout(
                    paper_bgcolor="#000000", height=(153 if _latest_corr < _CORR_THRESHOLD else 155),
                    margin=dict(t=1, b=1, l=8, r=8),
                    font=dict(family="monospace"),
                    # Cartesian axes for the needle overlay — scaleanchor keeps the angle correct at any container width
                    xaxis=dict(visible=False, range=[-1, 1], domain=[0, 1], scaleanchor="y", scaleratio=1),
                    # y=0 is the gauge pivot — range is lowered so the pivot lines up with the actual arc center
                    yaxis=dict(visible=False, range=[-0.10, 0.95], domain=[0.13, 0.87]),
                    annotations=[
                        dict(text=title, x=0.5, y=1.04, xref="paper", yref="paper", showarrow=False, xanchor="center", yanchor="top", font=dict(color="#B026FF", size=13, family="monospace")),
                        dict(text=f"{val}%", x=0.5, y=0.07, xref="paper", yref="paper", showarrow=False, xanchor="center", yanchor="middle", font=dict(color=_c, size=18, family="monospace")),
                    ]
                )
                return fig

            # Grabs the top 2 tickers by Exposure to show their 30-day volatility — df_p is already sorted descending
            _v_top2 = df_p["Ticker"].head(2).tolist() if not df_p.empty else []
            _gauge_specs = []
            for _vt in _v_top2:
                _vval = market_data.get_volatility_30d(_vt)
                _gauge_specs.append((_vval, f"{_vt} \u2014 30D Volatility"))
            while len(_gauge_specs) < 2:
                _gauge_specs.append((0.0, "\u2014 30D Volatility"))
            for _gi, (_gval, _gtitle) in enumerate(_gauge_specs):
                st.plotly_chart(_gauge(_gval, _gtitle, ""), use_container_width=True, config={"displayModeBar": False, "staticPlot": True}, key=f"pulse_gauge_{_gi}")
            _spacer = go.Figure()
            _spacer.update_layout(paper_bgcolor="#000000", height=(25 if _latest_corr < _CORR_THRESHOLD else 29), margin=dict(t=0,b=0,l=0,r=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(_spacer, use_container_width=True, config={"displayModeBar": False}, key="pulse_gauge_spacer")
    st.markdown('<div class="pulse-footer">© 2026 Pulse &nbsp;·&nbsp; All Rights Reserved</div>', unsafe_allow_html=True)
