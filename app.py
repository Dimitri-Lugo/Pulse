import streamlit as st
import db_ops
import dashboard
import base64
import os
import re
import secrets as _secrets
import resend
from datetime import datetime, timedelta
from cookie_utils import get_cookie_manager

# Builds and sends the password reset email using the Resend API
# Embeds the logo as base64 so it shows up inline without needing a hosted image URL
def send_recovery_email(target_email: str, reset_token: str) -> tuple[bool, str]:
    subject = "Pulse Risk Intelligence Platform - Password Reset"
    username = target_email.split("@")[0].replace(".", " ").replace("_", " ").title()
    try:
        app_url = st.secrets["APP_URL"]
    except Exception:
        app_url = "http://localhost:8501"
    _logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logo.png")
    if os.path.exists(_logo_path):
        with open(_logo_path, "rb") as _f:
            _logo_b64 = base64.b64encode(_f.read()).decode()
        logo_src = f"data:image/png;base64,{_logo_b64}"
    else:
        logo_src = ""
    html_body = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
  @-webkit-keyframes pulse-aura {{
    0%,100% {{ -webkit-box-shadow: 0 0 22px 8px rgba(157,0,255,0.65), 0 0 55px 20px rgba(157,0,255,0.35), 0 0 90px 35px rgba(157,0,255,0.15); box-shadow: 0 0 22px 8px rgba(157,0,255,0.65), 0 0 55px 20px rgba(157,0,255,0.35), 0 0 90px 35px rgba(157,0,255,0.15); }}
    50% {{ -webkit-box-shadow: 0 0 45px 18px rgba(157,0,255,1), 0 0 100px 40px rgba(157,0,255,0.6), 0 0 160px 65px rgba(157,0,255,0.25); box-shadow: 0 0 45px 18px rgba(157,0,255,1), 0 0 100px 40px rgba(157,0,255,0.6), 0 0 160px 65px rgba(157,0,255,0.25); }}
  }}
  @keyframes pulse-aura {{
    0%,100% {{ -webkit-box-shadow: 0 0 22px 8px rgba(157,0,255,0.65), 0 0 55px 20px rgba(157,0,255,0.35), 0 0 90px 35px rgba(157,0,255,0.15); box-shadow: 0 0 22px 8px rgba(157,0,255,0.65), 0 0 55px 20px rgba(157,0,255,0.35), 0 0 90px 35px rgba(157,0,255,0.15); }}
    50% {{ -webkit-box-shadow: 0 0 45px 18px rgba(157,0,255,1), 0 0 100px 40px rgba(157,0,255,0.6), 0 0 160px 65px rgba(157,0,255,0.25); box-shadow: 0 0 45px 18px rgba(157,0,255,1), 0 0 100px 40px rgba(157,0,255,0.6), 0 0 160px 65px rgba(157,0,255,0.25); }}
  }}
  @-webkit-keyframes pulse-text {{
    0%,100% {{ -webkit-text-shadow: 0 0 12px rgba(157,0,255,0.8), 0 0 28px rgba(157,0,255,0.4); text-shadow: 0 0 12px rgba(157,0,255,0.8), 0 0 28px rgba(157,0,255,0.4); }}
    50% {{ -webkit-text-shadow: 0 0 24px rgba(157,0,255,1), 0 0 55px rgba(157,0,255,0.7), 0 0 90px rgba(157,0,255,0.3); text-shadow: 0 0 24px rgba(157,0,255,1), 0 0 55px rgba(157,0,255,0.7), 0 0 90px rgba(157,0,255,0.3); }}
  }}
  @keyframes pulse-text {{
    0%,100% {{ text-shadow: 0 0 12px rgba(157,0,255,0.8), 0 0 28px rgba(157,0,255,0.4); }}
    50% {{ text-shadow: 0 0 24px rgba(157,0,255,1), 0 0 55px rgba(157,0,255,0.7), 0 0 90px rgba(157,0,255,0.3); }}
  }}
  .logo-aura {{
    -webkit-animation: pulse-aura 3s ease-in-out infinite;
    -moz-animation: pulse-aura 3s ease-in-out infinite;
    animation: pulse-aura 3s ease-in-out infinite;
  }}
  .pulse-title {{
    -webkit-animation: pulse-text 3s ease-in-out infinite;
    -moz-animation: pulse-text 3s ease-in-out infinite;
    animation: pulse-text 3s ease-in-out infinite;
  }}
  @-webkit-keyframes radial-glow {{
    0%,100% {{ opacity: 0.55; }}
    50% {{ opacity: 1; }}
  }}
  @keyframes radial-glow {{
    0%,100% {{ opacity: 0.55; }}
    50% {{ opacity: 1; }}
  }}
  .glow-layer {{
    -webkit-animation: radial-glow 3s ease-in-out infinite;
    -moz-animation: radial-glow 3s ease-in-out infinite;
    animation: radial-glow 3s ease-in-out infinite;
  }}
</style>
</head>
<body style="margin:0;padding:0;background-color:#000000;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#000000;">
  <tr><td align="center" style="padding:32px 16px;">
    <table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;border-radius:14px;overflow:hidden;border:1px solid #2a0845;">

      <!-- HEADER -->
      <tr>
        <td align="center" style="background-color:#000000;padding:0;border-bottom:1px solid #2a0845;">
          <!-- Radial glow layer rising from bottom-center -->
          <div class="glow-layer" style="display:block;width:100%;height:260px;margin-bottom:-260px;line-height:0;font-size:0;background:radial-gradient(ellipse at 50% 100%, rgba(157,0,255,0.85) 0%, rgba(157,0,255,0.55) 22%, rgba(157,0,255,0.28) 45%, rgba(157,0,255,0.1) 65%, transparent 80%);"></div>
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td align="center" style="padding:44px 32px 20px;">
                <div class="logo-aura" style="display:inline-block;border-radius:50%;padding:16px;background:radial-gradient(circle,rgba(157,0,255,0.75) 0%,rgba(157,0,255,0.35) 40%,rgba(157,0,255,0.12) 65%,transparent 80%);-webkit-box-shadow:0 0 28px 10px rgba(157,0,255,0.7),0 0 65px 25px rgba(157,0,255,0.4),0 0 110px 45px rgba(157,0,255,0.18);box-shadow:0 0 28px 10px rgba(157,0,255,0.7),0 0 65px 25px rgba(157,0,255,0.4),0 0 110px 45px rgba(157,0,255,0.18);">
                  {'<img src="' + logo_src + '" width="54" height="54" style="display:block;border-radius:10px;">' if logo_src else '<div style="width:54px;height:54px;background:linear-gradient(145deg,#9D00FF,#5a0099);border-radius:10px;"></div>'}
                </div>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:0 32px 8px;">
                <p class="pulse-title" style="color:#9D00FF;font-size:30px;font-weight:900;letter-spacing:7px;margin:0;text-shadow:0 0 14px rgba(157,0,255,0.85),0 0 32px rgba(157,0,255,0.4);">PULSE</p>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:0 32px 48px;">
                <p style="color:#5c4478;font-size:10px;letter-spacing:3.5px;text-transform:uppercase;margin:0;">RISK INTELLIGENCE PLATFORM</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- BODY -->
      <tr>
        <td style="background-color:#09090f;padding:36px 40px 28px;">
          <p style="color:#e8e8f0;font-size:15px;margin:0 0 18px;line-height:1.5;">Hi <strong style="color:#9D00FF;">{username}</strong>,</p>
          <p style="color:#9090a8;font-size:13px;line-height:1.75;margin:0 0 32px;">We received a request to reset the password associated with your Pulse account. If you made this request, click the button below to set a new password. This link is time-sensitive and will expire shortly.</p>

          <!-- BUTTON -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:32px;">
            <tr>
              <td align="center">
                <!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{app_url}?token={reset_token}&amp;email={target_email}" style="height:50px;v-text-anchor:middle;width:280px;" arcsize="18%" stroke="f" fillcolor="#9D00FF"><w:anchorlock/><center style="color:#ffffff;font-family:Arial,sans-serif;font-size:13px;font-weight:800;letter-spacing:2.5px;">RESET MY PASSWORD</center></v:roundrect><![endif]-->
                <!--[if !mso]><!-->
                <a href="{app_url}?token={reset_token}&amp;email={target_email}"
                   style="display:inline-block;background-color:#9D00FF;color:#ffffff;text-decoration:none;font-size:13px;font-weight:800;letter-spacing:2.5px;font-family:Arial,sans-serif;padding:15px 52px;border-radius:9px;-webkit-border-radius:9px;-moz-border-radius:9px;mso-hide:all;">RESET MY PASSWORD</a>
                <!--<![endif]-->
              </td>
            </tr>
          </table>

          <!-- DIVIDER -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px;">
            <tr><td height="1" style="height:1px;max-height:1px;background-color:#9D00FF;font-size:0;line-height:0;mso-line-height-rule:exactly;overflow:hidden;"></td></tr>
          </table>

          <!-- WARNING BOX -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">
            <tr>
              <td style="background-color:#130828;border:2px solid #9D00FF;border-radius:6px;padding:14px 18px;">
                <p style="margin:0;font-size:12px;line-height:1.7;color:#7a5a9a;"><strong style="color:#9D00FF;">Did not request this?</strong> If you did not request a password reset, you can safely ignore this email. Your password will remain unchanged. If you believe your account has been compromised, please contact support immediately.</p>
              </td>
            </tr>
          </table>

          <!-- EXPIRY -->
          <p style="color:#9D00FF;font-size:12px;text-align:center;margin:20px 0 0;font-style:italic;">This link expires in <strong style="color:#9D00FF;">15 minutes</strong>.</p>
        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td align="center" style="background-color:#000000;padding:22px 40px;border-top:1px solid #1e0a33;">
          <p style="color:#9D00FF;font-size:12px;margin:0 0 6px;">&#169; 2026 <strong style="color:#9D00FF;">Pulse</strong> &nbsp;&#183;&nbsp; All Rights Reserved</p>
          <p style="color:#9D00FF;font-size:11px;margin:0 0 8px;">You are receiving this email because a password reset was requested for your account.</p>
          <a href="#" style="color:#9D00FF;font-size:11px;text-decoration:underline;">Unsubscribe</a>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body></html>"""
    try:
        resend.api_key = st.secrets["RESEND_API_KEY"]
        resend.Emails.send({
            "from": "Pulse <onboarding@resend.dev>",
            "to": [target_email],
            "subject": subject,
            "html": html_body,
        })
        return True, ""
    except Exception as e:
        return False, str(e)

st.set_page_config(page_title="Pulse", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@keyframes pulse-glow {
    0%, 100% { text-shadow: 0 0 8px rgba(157,0,255,0.75), 0 0 20px rgba(157,0,255,0.4); }
    50% { text-shadow: 0 0 18px rgba(157,0,255,1), 0 0 45px rgba(157,0,255,0.75), 0 0 90px rgba(157,0,255,0.35); }
}
@keyframes logo-aura-pulse {
    0%, 100% { transform: scale(0.8); opacity: 0.4; }
    50% { transform: scale(1.6); opacity: 0.9; }
}
@keyframes card-aura {
    0%, 100% { box-shadow: 0 0 18px rgba(157,0,255,0.1), 0 4px 28px rgba(0,0,0,0.65); }
    50% { box-shadow: 0 0 55px rgba(157,0,255,0.28), 0 0 110px rgba(157,0,255,0.1), 0 4px 28px rgba(0,0,0,0.65); }
}
* { box-sizing: border-box !important; }
html, body, .stApp {
    overflow: hidden !important;
    height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    background-color: #000000 !important;
}
[data-testid="stAppViewContainer"], [data-testid="stToolbar"],
section.main { background-color: #000000 !important; }
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none; }
footer { visibility: hidden; }
#pulse-auth-container,
.stApp div[data-testid="block-container"] {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    width: 320px !important;
    z-index: 9999 !important;
    border: 1px solid #9D00FF !important;
    border-radius: 12px !important;
    background-color: #0b0b0f !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    padding: 0 !important;
    animation: card-aura 4s ease-in-out infinite;
}
.stApp div[data-testid="block-container"] > div { padding: 1rem 1.5rem 1rem !important; }
[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"] > div:last-child {
    display: flex !important;
    justify-content: flex-end !important;
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"] > div:last-child div[data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: stretch !important;
    width: 100% !important;
    height: 100% !important;
}
[data-testid="stHorizontalBlock"] > div:last-child div[data-testid="stElementContainer"] {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-end !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    width: 100% !important;
}
[data-testid="stHorizontalBlock"] > div:last-child button {
    margin-left: auto !important;
}
.logo-wrap { display: flex; justify-content: center; margin-bottom: 0.4rem; }
.logo-aura-wrap { position: relative; display: flex; align-items: center; justify-content: center; width: 54px; height: 54px; }
.logo-aura {
    position: absolute; inset: 0; border-radius: 50%;
    background: radial-gradient(circle, rgba(157,0,255,0.85) 0%, rgba(157,0,255,0.35) 45%, transparent 72%);
    animation: logo-aura-pulse 3s ease-in-out infinite;
    z-index: 0;
}
.logo-img { position: relative; z-index: 1; width: 46px; height: 46px; object-fit: contain; mix-blend-mode: screen; }
.logo-box {
    position: relative; z-index: 1;
    width: 52px; height: 52px;
    background: linear-gradient(145deg, #9D00FF 0%, #6a00b0 100%);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem; font-weight: 800; color: #fff;
}
.pulse-title {
    font-size: 1.4rem; font-weight: 700; color: #9D00FF;
    text-align: center; letter-spacing: 0.22em; margin: 0 0 0.15rem;
    animation: pulse-glow 3s ease-in-out infinite;
}
.pulse-tagline {
    font-size: 0.58rem; color: #6b5580; text-align: center;
    letter-spacing: 0.18em; margin: 0 0 0.4rem; text-transform: uppercase;
}
.auth-divider { border: none; border-top: 1px solid #1e0a33; margin: 0 0 0.5rem; }
.input-label { font-size: 0.63rem; color: #9D00FF; font-weight: 600; letter-spacing: 0.1em; margin-bottom: 0.2rem; display: block; }
div[data-baseweb="input"] {
    background-color: #000000 !important;
    border: 1px solid #9D00FF !important;
    border-radius: 7px !important;
    box-shadow: none !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #9D00FF !important;
    box-shadow: 0 0 0 2px rgba(157,0,255,0.2) !important;
    outline: none !important;
}
div[data-baseweb="input"] > div { background-color: transparent !important; border: none !important; }
div[data-testid="stTextInput"] input {
    background-color: #000000 !important;
    border: none !important;
    color: #d4d4d4 !important;
    padding: 0.5rem 0.75rem !important;
    font-size: 0.9rem !important;
    box-shadow: none !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #3d3050 !important; }
[data-testid="stCheckbox"] label p { color: #7a6a90 !important; font-size: 0.8rem !important; }
button[kind="primary"],
[data-testid="baseButton-primary"],
[data-testid="stBaseButton-primary"] {
    background-color: #9D00FF !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.12em !important;
    width: 100% !important;
    padding: 0.65rem 1rem !important;
    transition: background 0.2s, box-shadow 0.2s !important;
}
button[kind="primary"]:hover,
[data-testid="baseButton-primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
    background-color: #b030ff !important;
    box-shadow: 0 0 22px rgba(157,0,255,0.55) !important;
}
button[kind="secondary"],
[data-testid="baseButton-secondary"],
[data-testid="stBaseButton-secondary"] {
    background-color: transparent !important;
    color: #7a6a90 !important;
    border: 1px solid #2d0a52 !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    width: 100% !important;
    padding: 0.6rem 1rem !important;
    transition: border-color 0.2s, color 0.2s !important;
}
button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {
    border-color: #9D00FF !important;
    color: #9D00FF !important;
    background-color: rgba(157,0,255,0.05) !important;
}
.stButton > button { box-shadow: none !important; }
.stButton > button:focus { outline: none !important; box-shadow: none !important; }
[data-testid="stAlert"] { border-radius: 8px !important; }
[data-testid="stHorizontalBlock"] > div:last-child button {
    font-size: 0.75rem !important;
    padding: 0 !important;
    width: auto !important;
    min-height: 0 !important;
    line-height: 1.2 !important;
    margin-left: auto !important;
}
button[kind="tertiary"],
[data-testid="baseButton-tertiary"],
[data-testid="stBaseButton-tertiary"] {
    color: #B026FF !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    font-size: 0.75rem !important;
}
button[kind="tertiary"]:hover,
[data-testid="baseButton-tertiary"]:hover,
[data-testid="stBaseButton-tertiary"]:hover {
    color: #cc44ff !important;
    text-decoration: underline !important;
    background: transparent !important;
}
.pulse-footer {
    position: fixed !important; bottom: 20px !important; left: 0 !important;
    width: 100% !important; text-align: center !important; z-index: 1000 !important;
    font-size: 0.65rem; color: #8a6aaa; letter-spacing: 0.08em;
    pointer-events: none;
}
/* ── HIGH alert card button ───────────────────────────────────────────────── */
html body .stApp [class*="st-key-btn_rf_high"] button {
    background: rgba(255,0,127,0.06) !important;
    border: 1px solid #FF007F !important;
    border-left: 3px solid #FF007F !important;
    border-radius: 6px !important;
    padding: 11px 14px !important;
    width: 108% !important;
    min-height: 62px !important;
    height: auto !important;
    text-align: left !important;
    box-shadow: 0 0 10px rgba(255,0,127,0.15) !important;
    cursor: pointer !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 3px !important;
    white-space: normal !important;
    overflow: visible !important;
}
html body .stApp [class*="st-key-btn_rf_high"] button:hover {
    background: rgba(255,0,127,0.12) !important;
    box-shadow: 0 0 18px rgba(255,0,127,0.28) !important;
}
html body .stApp [class*="st-key-btn_rf_high"] button p {
    color: #FF007F !important;
    font-family: monospace !important;
    font-size: 0.65rem !important;
    text-align: left !important;
    margin: 0 !important;
    line-height: 1.3 !important;
    font-weight: 500 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
}
html body .stApp [class*="st-key-btn_rf_high"] button p:first-of-type::before {
    content: "HIGH";
    background: #FF007F;
    color: #fff;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.60rem;
    margin-right: 7px;
    vertical-align: middle;
    letter-spacing: 0.05em;
}
html body .stApp [class*="st-key-btn_rf_high"] button p:last-of-type {
    color: #a04060 !important;
    font-size: 0.58rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.02em !important;
}
/* Hide browser-native password reveal button (Edge / Chrome) */
input[type="password"]::-ms-reveal,
input[type="password"]::-ms-clear,
input[type="password"]::-webkit-credentials-auto-fill-button {
    display: none !important;
}
/* Disable text selection globally except in inputs / textareas */
body, .stApp, [data-testid="stAppViewContainer"] {
    -webkit-user-select: none !important;
    -moz-user-select: none !important;
    -ms-user-select: none !important;
    user-select: none !important;
}
input, textarea, [contenteditable="true"] {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
/* Portfolio form — Ticker & Shares/Tokens placeholder colour */
html body .stApp [class*="st-key-pulse_portfolio_card"] input::placeholder {color:#A99BB8 !important;opacity:1 !important;}
html body .stApp [class*="st-key-pulse_portfolio_card"] input::-webkit-input-placeholder {color:#A99BB8 !important;opacity:1 !important;}
html body .stApp [class*="st-key-pulse_portfolio_card"] input::-moz-placeholder {color:#A99BB8 !important;opacity:1 !important;}
html body .stApp [class*="st-key-pulse_portfolio_card"] input:-ms-input-placeholder {color:#A99BB8 !important;opacity:1 !important;}
html body .stApp [class*="st-key-pulse_portfolio_card"] [data-baseweb="input"] input::placeholder {color:#A99BB8 !important;opacity:1 !important;}
/* Suppress Streamlit's stale-content fade during fragment auto-reruns */
[data-stale="true"], [data-stale] {
    opacity: 1 !important;
    transition: none !important;
}
.stApp.running [data-testid="stMain"],
.stApp.running [data-testid="stAppViewContainer"],
.stApp.running [data-testid="stMainBlockContainer"],
.stApp.running [data-testid="block-container"] {
    opacity: 1 !important;
    transition: none !important;
}
</style>
""", unsafe_allow_html=True)

# Sets up all the database tables on startup — safe to call every time due to IF NOT EXISTS
db_ops.init_db()

# Renders the cookie manager component on every rerun so the app can read and write browser cookies
cookie_manager = get_cookie_manager()

# On the very first script run the cookie manager hasn't read the browser yet and returns {}
# Stops here so Streamlit reruns immediately once the real cookie data comes back from the browser
# This prevents the login screen from flashing before the app knows the user's cookie state
if not st.session_state.get("_cookie_checked"):
    st.session_state["_cookie_checked"] = True
    st.stop()

# Writes the auth token cookie on the rerun after a successful login, not during the login itself
_pending_set = st.session_state.pop("_pending_token_set", None)
if _pending_set:
    cookie_manager.set(
        "pulse_auth_token",
        _pending_set,
        key="set_token",
        expires_at=datetime.now() + timedelta(days=30),
    )

# Saves the email to a cookie so the login form is pre-filled on future visits when "Remember me" was checked
_pending_email = st.session_state.pop("_pending_email_remember", None)
if _pending_email:
    cookie_manager.set(
        "pulse_remembered_email",
        _pending_email,
        key="set_email",
        expires_at=datetime.now() + timedelta(days=365),
    )

# Deletes the auth token cookie on the rerun after logout so the session is fully cleared
if st.session_state.pop("_pending_cookie_delete", False):
    cookie_manager.delete("pulse_auth_token")

# Checks if there's a saved session cookie and logs the user in automatically without showing the login screen
if not st.session_state.get("authenticated"):
    _stored_token = cookie_manager.get("pulse_auth_token")
    if _stored_token:
        _token_email = db_ops.verify_auth_token(_stored_token)
        if _token_email:
            st.session_state["authenticated"] = True
            st.session_state["username"] = _token_email
            st.session_state["_auth_token"] = _stored_token
            st.session_state["nickname"] = db_ops.get_nickname(_token_email)
            st.session_state["role"] = db_ops.get_role(_token_email)
            st.session_state["profile_pic"] = db_ops.get_profile_pic(_token_email)

if "username" not in st.session_state:
    st.session_state["username"] = ""

# Pre-fills the email field from the "Remember me" cookie before the widget renders
# Only runs if the field is currently blank — won't overwrite anything the user typed
if not st.session_state.get("authenticated") and not st.session_state.get("username"):
    _rem = cookie_manager.get("pulse_remembered_email")
    if _rem:
        st.session_state["username"] = _rem

# Loads the logo to embed it inline in the login page header
_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logo.png")
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()
    _logo_html = f'<div class="logo-aura-wrap"><div class="logo-aura"></div><img src="data:image/png;base64,{_logo_b64}" class="logo-img"></div>'
else:
    _logo_html = '<div class="logo-aura-wrap"><div class="logo-aura"></div><div class="logo-box">P</div></div>'

# Sets up all the session state variables before any widgets are rendered
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "login"
if "remember_me" not in st.session_state:
    st.session_state["remember_me"] = bool(st.session_state.get("_auth_token"))
if "_reset_token" not in st.session_state:
    st.session_state["_reset_token"] = ""
if "_reset_email" not in st.session_state:
    st.session_state["_reset_email"] = ""
if "_pending_success" not in st.session_state:
    st.session_state["_pending_success"] = ""
# Checks the URL for special query params — the forgot password link sets ?forgot=1
# and the reset email link includes ?token=...&email=...
if st.query_params.get("forgot") == "1":
    st.query_params.clear()
    st.session_state["current_page"] = "forgot_password"
    st.rerun()
elif "token" in st.query_params and "email" in st.query_params:
    _qp_token = st.query_params.get("token")
    _qp_email = st.query_params.get("email")
    _verified = db_ops.verify_reset_token(_qp_token)
    if _verified:
        st.session_state["current_page"] = "reset_password"
        st.session_state["_reset_token"] = _qp_token
        st.session_state["_reset_email"] = _qp_email
    else:
        st.session_state["current_page"] = "login"
    st.query_params.clear()
    st.rerun()

# If the user is already logged in, skips the login page and goes straight to the dashboard
if st.session_state["authenticated"]:
    dashboard.render_dashboard()
    st.stop()

# Everything below this point is the login / register / password reset UI
with st.container():
    st.markdown(f'<div class="logo-wrap">{_logo_html}</div>', unsafe_allow_html=True)
    st.markdown('<p class="pulse-title">PULSE</p>', unsafe_allow_html=True)
    st.markdown('<p class="pulse-tagline">Risk Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)
    if st.session_state.get("_pending_success"):
        st.success(st.session_state["_pending_success"])
        st.session_state["_pending_success"] = ""
    if st.session_state["current_page"] == "forgot_password":
        st.markdown('<span class="input-label">EMAIL</span>', unsafe_allow_html=True)
        reset_email = st.text_input("reset_email", placeholder="you@example.com", key="reset_email", label_visibility="collapsed")
        if st.button("Send Password Reset", use_container_width=True, type="primary", key="btn_send_reset"):
            if not reset_email:
                st.error("Please enter your email address.")
            else:
                _tok = _secrets.token_urlsafe(32)
                db_ops.store_reset_token(reset_email.strip(), _tok)
                ok, err = send_recovery_email(reset_email.strip(), _tok)
                if ok:
                    st.session_state["_pending_success"] = "Recovery email sent. Please check your inbox."
                    st.session_state["current_page"] = "login"
                    st.rerun()
                else:
                    st.error(f"Failed to send email: {err}")
        if st.button("Back to Login", use_container_width=True, type="tertiary", key="btn_back_login"):
            st.session_state["current_page"] = "login"
            st.rerun()
    elif st.session_state["current_page"] == "reset_password":
        if not st.session_state["_reset_token"]:
            st.error("Invalid or expired reset link.")
            if st.button("Back to Login", use_container_width=True, type="tertiary", key="btn_invalid_back"):
                st.session_state["current_page"] = "login"
                st.rerun()
        else:
            st.markdown('<p style="color:#9D00FF;font-size:1.1rem;font-weight:700;text-align:center;letter-spacing:0.04em;margin:0.4rem 0 0.3rem 0;">Set a New Password</p>', unsafe_allow_html=True)
            st.markdown('<p style="color:#6b5580;font-size:0.78rem;text-align:center;line-height:1.55;margin:0 0 1rem 0;">Your identity has been verified. Choose a strong<br>new password for your account.</p>', unsafe_allow_html=True)
            st.markdown('<span class="input-label">NEW PASSWORD</span>', unsafe_allow_html=True)
            new_pw = st.text_input("new_pw", type="password", placeholder="••••••••", key="new_pw", label_visibility="collapsed")
            st.markdown('<span class="input-label">CONFIRM PASSWORD</span>', unsafe_allow_html=True)
            confirm_pw = st.text_input("confirm_pw", type="password", placeholder="••••••••", key="confirm_pw", label_visibility="collapsed")
            st.markdown("""
<div style="background:#0d0818;border-left:3px solid #9D00FF;border-radius:0 4px 4px 0;padding:10px 14px;margin:0.5rem 0 0.9rem;">
<ul style="margin:0;padding-left:1.1em;color:#9D00FF;font-size:0.74rem;line-height:2;list-style:disc;">
<li>At least 8 characters</li>
<li>One uppercase letter</li>
<li>One number</li>
<li>One special character (!@#$...)</li>
</ul></div>""", unsafe_allow_html=True)
            if st.button("UPDATE PASSWORD", use_container_width=True, type="secondary", key="btn_update_pw"):
                _errs = []
                if not new_pw:
                    st.error("Please enter a new password.")
                elif new_pw != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    if len(new_pw) < 8:
                        _errs.append("at least 8 characters")
                    if not re.search(r'[A-Z]', new_pw):
                        _errs.append("one uppercase letter")
                    if not re.search(r'[0-9]', new_pw):
                        _errs.append("one number")
                    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', new_pw):
                        _errs.append("one special character (!@#$...)")
                    if _errs:
                        st.error("Password must contain: " + ", ".join(_errs) + ".")
                    else:
                        if db_ops.update_password(st.session_state["_reset_email"], new_pw):
                            db_ops.consume_reset_token(st.session_state["_reset_token"])
                            st.session_state["_reset_token"] = ""
                            st.session_state["_reset_email"] = ""
                            st.session_state["_pending_success"] = "Password updated successfully. Please sign in."
                            st.session_state["current_page"] = "login"
                            st.rerun()
                        else:
                            st.error("Account not found. Please try again.")
            if st.button("← Back to Sign In", use_container_width=True, type="tertiary", key="btn_back_signin_reset"):
                st.session_state["_reset_token"] = ""
                st.session_state["_reset_email"] = ""
                st.session_state["current_page"] = "login"
                st.rerun()
    else:
        if st.session_state["current_page"] == "register":
            st.markdown('<span class="input-label">NICKNAME</span>', unsafe_allow_html=True)
            reg_nickname = st.text_input("nickname", placeholder="Up to 12 characters", key="reg_nickname", label_visibility="collapsed", max_chars=12)
        st.markdown('<span class="input-label">EMAIL</span>', unsafe_allow_html=True)
        username = st.text_input("email", placeholder="you@example.com", key="username", label_visibility="collapsed")
        st.markdown('<span class="input-label">PASSWORD</span>', unsafe_allow_html=True)
        password = st.text_input("password", type="password", placeholder="••••••••", key="password", label_visibility="collapsed")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.session_state["remember_me"] = st.checkbox("Remember me", value=st.session_state["remember_me"], key="remember")
        with col2:
            if st.session_state["current_page"] == "login":
                st.markdown(
                    '<style>'
                    '[data-testid="stHorizontalBlock"]{align-items:stretch!important}'
                    '[data-testid="stHorizontalBlock"]>div:last-child{display:flex!important;align-items:stretch!important;justify-content:flex-end!important}'
                    '[data-testid="stHorizontalBlock"]>div:last-child [data-testid="stVerticalBlock"]{display:flex!important;flex-direction:column!important;justify-content:center!important;align-items:stretch!important;height:100%!important;width:100%!important}'
                    '[data-testid="stHorizontalBlock"]>div:last-child [data-testid="stElementContainer"]{display:flex!important;align-items:center!important;justify-content:flex-end!important;padding-top:0!important;padding-bottom:0!important;width:100%!important}'
                    '.fpw-row{width:100%;display:flex;justify-content:flex-end;align-items:center}'
                    '</style>'
                    '<div class="fpw-row">'
                    '<a href="?forgot=1" style="color:#9D00FF;font-size:0.75rem;font-weight:600;'
                    'letter-spacing:0.06em;text-decoration:none;white-space:nowrap;">Forgot password?</a>'
                    '</div>',
                    unsafe_allow_html=True
                )
        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
        if st.session_state["current_page"] == "register":
            if st.button("REGISTER", use_container_width=True, type="primary", key="btn_register"):
                _nick_val = st.session_state.get("reg_nickname", "").strip()
                if not username or not password:
                    st.error("Please fill in all fields.")
                elif not _nick_val:
                    st.error("Please choose a nickname.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif db_ops.register_user(username.strip(), password, _nick_val):
                    st.success("Account created successfully. Please sign in.")
                    st.session_state["current_page"] = "login"
                    st.rerun()
                else:
                    st.error("An account with that email already exists.")
        else:
            if st.button("SIGN IN", use_container_width=True, type="primary", key="btn_signin"):
                if not username or not password:
                    st.error("Please enter your email and password.")
                elif db_ops.verify_user(username.strip(), password):
                    _token = db_ops.create_auth_token(username.strip())
                    st.session_state["authenticated"] = True
                    st.session_state["_auth_token"] = _token
                    st.session_state["nickname"] = db_ops.get_nickname(username.strip())
                    st.session_state["role"] = db_ops.get_role(username.strip())
                    st.session_state["profile_pic"] = db_ops.get_profile_pic(username.strip())
                    # Always saves the token cookie so the user stays logged in after a page refresh
                    st.session_state["_pending_token_set"] = _token
                    # If "Remember me" is checked, also saves the email so the login form is pre-filled next time
                    if st.session_state.get("remember_me"):
                        st.session_state["_pending_email_remember"] = username.strip()
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
        st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
        if st.session_state["current_page"] == "register":
            if st.button("Already have an account? Sign In", key="switch_signin", use_container_width=True, type="secondary"):
                st.session_state["current_page"] = "login"
                st.rerun()
        else:
            if st.button("Register an Account", key="switch_register", use_container_width=True, type="secondary"):
                st.session_state["current_page"] = "register"
                st.rerun()

st.markdown(
    '<div class="pulse-footer">© 2026 Pulse &nbsp;·&nbsp; All Rights Reserved</div>',
    unsafe_allow_html=True,
)
