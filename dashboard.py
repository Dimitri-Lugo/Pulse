import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
import os
import io
from PIL import Image

def render_dashboard():
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
    .stApp [data-testid="stTextInput"] input{background:#070010!important;color:#ddc8ff!important;border:1px solid #3a0075!important;border-radius:5px!important;font-size:0.76rem!important;font-family:monospace!important;padding:0.28rem 0.5rem!important;}
    .stApp [data-testid="stTextInput"] input:focus{border-color:#B026FF!important;box-shadow:0 0 7px rgba(176,38,255,0.4)!important;}
    .stApp [data-testid="stTextInput"] label{display:none!important;}
    html body .stApp button[data-testid="stBaseButton-primary"],html body .stApp [data-testid="stBaseButton-primary"]{background-color:#B026FF!important;background:#B026FF!important;border:none!important;font-family:monospace!important;letter-spacing:0.1em!important;font-size:0.7rem!important;font-weight:800!important;padding:0.4rem 0.6rem!important;border-radius:6px!important;min-height:36px!important;box-shadow:0 0 10px rgba(176,38,255,0.55)!important;color:#ffffff!important;}
    html body .stApp button[data-testid="stBaseButton-primary"]:hover,html body .stApp [data-testid="stBaseButton-primary"]:hover{background-color:#9a00dd!important;background:#9a00dd!important;box-shadow:0 0 18px rgba(176,38,255,0.8)!important;}
    html body .stApp button[data-testid="stBaseButton-primary"] *,html body .stApp [data-testid="stBaseButton-primary"] *{color:#ffffff!important;font-weight:800!important;}
    .stElementToolbar,[data-testid="StyledFullScreenButton"],[data-testid="stBaseButton-headerNoPadding"]{display:none!important;}
    [data-testid="stDataFrame"] thead th{background:#080018!important;color:#B026FF!important;font-size:0.59rem!important;font-family:monospace!important;letter-spacing:0.1em!important;border-bottom:1px solid rgba(157,0,255,0.4)!important;}
    [data-testid="stDataFrame"] tbody td{color:#c8a8e8!important;font-size:0.72rem!important;background:#03000a!important;font-family:monospace!important;}
    [data-testid="stDataFrame"] tbody tr:hover td{background:#0a0020!important;}
    [data-testid="stSegmentedControl"]{gap:0!important;}
    [data-testid="stSegmentedControl"] label{background:transparent!important;color:#3d2260!important;border:1px solid #1e0035!important;border-radius:4px!important;font-size:0.62rem!important;font-family:monospace!important;letter-spacing:0.06em!important;padding:3px 9px!important;transition:all 0.15s!important;}
    [data-testid="stSegmentedControl"] label:has(input:checked){background:#18003a!important;color:#B026FF!important;border-color:#B026FF!important;box-shadow:0 0 10px rgba(176,38,255,0.35)!important;}
    [data-testid="stToggle"] span[data-testid="stWidgetLabel"]{display:none!important;}
    [data-testid="stToggle"]>div>div{background-color:#B026FF!important;}
    div[data-testid="stHorizontalBlock"]{align-items:stretch!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]{display:flex!important;flex-direction:column!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] div[data-testid="stVerticalBlock"]{flex:1!important;display:flex!important;flex-direction:column!important;}
    div[data-testid="stColumn"]:not(:last-child) div[data-testid="stVerticalBlockBorderWrapper"]{flex:1!important;display:flex!important;flex-direction:column!important;height:auto!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:first-child{flex:0 0 auto!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:last-child{flex:1!important;display:flex!important;flex-direction:column!important;height:auto!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:first-child div[data-testid="stVerticalBlockBorderWrapper"]{min-height:560px!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:nth-child(2) div[data-testid="stVerticalBlockBorderWrapper"]{min-height:560px!important;}
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:last-child{min-height:260px!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:last-child div[data-testid="stVerticalBlock"]{gap:3px!important;}
    div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],div[data-testid="stColumn"]:last-child > div > div[data-testid="stVerticalBlock"]{padding-top:0!important;margin-top:0!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:first-child > div{padding:4px 6px!important;overflow:hidden!important;}
    div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]:first-child div[data-testid="stVerticalBlock"]{padding-left:0!important;padding-top:0!important;overflow:hidden!important;}
    .dh-center{color:#B026FF;font-size:0.65rem;font-weight:700;letter-spacing:0.16em;margin:0 0 0.5rem;font-family:monospace;text-transform:uppercase;text-align:center!important;width:100%!important;display:block!important;white-space:nowrap;}
    [data-testid="stVerticalBlock"]>[style*="flex-direction: column;"]>[data-testid="stVerticalBlock"]{gap:0.5rem!important;}
    </style>""", unsafe_allow_html=True)
    _vals = [12400, 9100, 18600, 6200, 3800, 10500, 8200, 5900, 3100, 14000, 9600, 2400, 1700, 6380, 2900, 7100, 4600]
    _tickers = ["TSLA","AAPL","NVDA","META","MSFT","AMZN","GOOGL","AMD","NFLX","SPY","QQQ","CRM","INTC","UBER","PYPL","COIN","PLTR"]
    if "portfolio" not in st.session_state:
        _max = max(_vals)
        st.session_state["portfolio"] = {
            "Ticker": _tickers,
            "Pct": [round(v / _max * 100) for v in _vals],
            "Value": [f"${v:,}" for v in _vals],
        }
    _uname = st.session_state.get("username", "user@pulse.com")
    _dname = _uname.split("@")[0].replace(".", " ").replace("_", " ").title()
    _initials = "".join([w[0].upper() for w in _dname.split()[:2]])[:2]
    _disp = " ".join(_dname.split()[:2])
    if len(_disp) > 12:
        _disp = _dname.split()[0] + " " + _dname.split()[1][0] + "." if len(_dname.split()) > 1 else _dname[:12]
    hc1, hc2, hc3 = st.columns([1, 1, 1])
    with hc1:
        st.markdown('<p class="pulse-text-animate" style="color:#B026FF;font-size:2rem;font-weight:900;letter-spacing:0.28em;margin:0;padding:0.2rem 0;font-family:monospace;">PULSE</p>', unsafe_allow_html=True)
    with hc2:
        st.markdown(f'<div style="display:flex;justify-content:center;align-items:center;padding:0.2rem 0;"><div style="padding:10px;background:transparent;">{_logo_img}</div></div>', unsafe_allow_html=True)
    with hc3:
        st.markdown(f'<div style="display:flex;justify-content:flex-end;align-items:center;padding:0.2rem 0;"><div style="background:#06000f;border:1px solid rgba(157,0,255,0.45);border-radius:8px;padding:6px 14px;display:inline-flex;align-items:center;gap:10px;"><div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#B026FF,#55007a);display:flex;align-items:center;justify-content:center;font-size:0.62rem;font-weight:700;color:#fff;flex-shrink:0;letter-spacing:0.03em;">{_initials}</div><div><p style="color:#B026FF;font-size:0.7rem;font-weight:700;margin:0;letter-spacing:0.04em;font-family:monospace;">{_disp}</p><p style="color:#3a2255;font-size:0.58rem;margin:0;font-family:monospace;">Risk Analyst &nbsp;&#9660;</p></div></div></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(157,0,255,0.5) 30%,rgba(157,0,255,0.5) 70%,transparent);margin:0.1rem 0 0.6rem;"></div>', unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1], gap="medium")
    with col_l:
        with st.container(border=True):
            st.markdown('<p class="dh">PORTFOLIO</p>', unsafe_allow_html=True)
            ic1, ic2, ic3 = st.columns([5, 5, 3])
            with ic1:
                t_in = st.text_input("tk", "", placeholder="Ticker", key="pt", label_visibility="collapsed")
            with ic2:
                a_in = st.text_input("am", "", placeholder="$ Amount", key="pa", label_visibility="collapsed")
            with ic3:
                add_clicked = st.button("ADD", use_container_width=True, type="primary", key="btn_add")
            if add_clicked and t_in and a_in:
                try:
                    amt = float(a_in.replace("$", "").replace(",", ""))
                    tk = t_in.upper().strip()
                    pf = st.session_state["portfolio"]
                    if tk not in pf["Ticker"]:
                        _cur_max = max(float(v.replace("$","").replace(",","")) for v in pf["Value"])
                        _new_max = max(amt, _cur_max)
                        pf["Pct"] = [round(float(pf["Value"][i].replace("$","").replace(",","")) / _new_max * 100) for i in range(len(pf["Ticker"]))]
                        pf["Ticker"].append(tk)
                        pf["Pct"].append(round(amt / _new_max * 100))
                        pf["Value"].append(f"${amt:,.0f}")
                        st.rerun()
                except ValueError:
                    st.error("Invalid amount.")
            df_p = pd.DataFrame(st.session_state["portfolio"])
            st.dataframe(df_p, column_config={
                "Ticker": st.column_config.TextColumn("Asset", width="small"),
                "Pct": st.column_config.ProgressColumn("", min_value=0, max_value=100, format=" "),
                "Value": st.column_config.TextColumn("$ Amount", width="small"),
            }, hide_index=True, use_container_width=True, height=460)
    with col_c:
        with st.container(border=True):
            st.markdown('<p class="dh">ANALYTICS</p>', unsafe_allow_html=True)
            timeframe = st.segmented_control("TF", ["7 Days", "30 Days", "90 Days", "1 Year"], default="30 Days", key="tf", label_visibility="collapsed")
            n = {"7 Days": 7, "30 Days": 30, "90 Days": 90, "1 Year": 365}.get(timeframe or "30 Days", 30)
            np.random.seed(7)
            t = np.linspace(0, 1, n)
            base = 0.22 + 0.42 * t
            oscillation = 0.06 * np.sin(t * np.pi * 3)
            surge = np.zeros(n)
            surge[-max(7, n // 5):] = np.linspace(0.0, 0.35, max(7, n // 5))
            noise = np.random.normal(0, 0.026, n)
            corr = np.clip(base + oscillation + surge + noise, 0.08, 1.0)
            if n <= 30:
                x_labels = [f"Day {i+1}" for i in range(n)]
                tick_vals = x_labels[::max(1, n // 5)]
            else:
                dates = pd.date_range(end=pd.Timestamp.today(), periods=n, freq="D")
                x_labels = dates.strftime("%b %d").tolist()
                tick_vals = x_labels[::max(1, n // 6)]
            st.markdown('<p style="color:#2e1650;font-size:0.56rem;letter-spacing:0.13em;font-family:monospace;margin:0.2rem 0 0.1rem;">RISK CORRELATION GRAPH</p>', unsafe_allow_html=True)
            fig_c = go.Figure()
            fig_c.add_trace(go.Scatter(x=x_labels, y=corr, mode="lines", line=dict(color="#B026FF", width=2.8, shape="spline"), fill="tozeroy", fillcolor="rgba(176,38,255,0.06)"))
            fig_c.update_layout(
                paper_bgcolor="#000000", plot_bgcolor="#030008",
                font=dict(color="#5a3a7a", family="monospace", size=9),
                margin=dict(l=44, r=12, t=8, b=52),
                xaxis=dict(gridcolor="#0d001c", zeroline=False, tickfont=dict(size=8, color="#3d2458"), tickvals=tick_vals, title=dict(text="Time", font=dict(size=8, color="#2a1545"))),
                yaxis=dict(gridcolor="#0d001c", zeroline=False, range=[0, 1.12], tickvals=[0.1, 0.4, 0.7, 1.0], ticktext=["0.1", "0.4", "0.7", "1.0"], tickfont=dict(size=8, color="#3d2458"), title=dict(text="Correlation Index", font=dict(size=8, color="#2a1545"))),
                showlegend=False, height=450,
                shapes=[dict(type="line", x0=x_labels[0], x1=x_labels[-1], y0=0.5, y1=0.5, line=dict(color="#FF007F", width=1.2, dash="dot"))],
            )
            st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})
    with col_r:
        with st.container(border=True):
            rc1, rc2 = st.columns([4, 1])
            with rc1:
                st.markdown('<p class="dh" style="margin-bottom:0.05rem;">RISK ALERT FEED</p>', unsafe_allow_html=True)
            with rc2:
                st.toggle("", value=True, key="live_toggle")
            st.markdown(
                '<div style="border:1px solid #B026FF;border-radius:8px;padding:5px 8px;margin-bottom:2px;">'
                '<div style="display:flex;justify-content:flex-start;align-items:center;gap:6px;margin-bottom:2px;">'
                '<div style="background:#B026FF;color:#ffffff;font-weight:bold;padding:2px 6px;border-radius:4px;font-size:0.62rem;white-space:nowrap;flex-shrink:0;">WARN</div>'
                '<span style="color:#B026FF;font-size:0.65rem;line-height:1.1;text-align:left;">Specific assets indicate dangerously high correlation.</span>'
                '</div>'
                '<div style="font-size:0.6rem;color:#6b4f82;line-height:1.1;text-align:left;">3 min ago &nbsp;·&nbsp; TSLA - NVDA</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="border:1px solid #FF007F;border-radius:8px;padding:5px 8px;">'
                '<div style="display:flex;justify-content:flex-start;align-items:center;gap:6px;margin-bottom:2px;">'
                '<div style="background:#FF007F;color:#ffffff;font-weight:bold;padding:2px 6px;border-radius:4px;font-size:0.62rem;white-space:nowrap;flex-shrink:0;">HIGH</div>'
                '<span style="color:#FF007F;font-size:0.65rem;line-height:1.1;text-align:left;">HIGH CORRELATION ALERT: TSLA/AAPL <span style="text-decoration:underline;cursor:pointer;">[View Details]</span></span>'
                '</div>'
                '<div style="font-size:0.6rem;color:#7a3050;line-height:1.1;text-align:left;">Just now &nbsp;·&nbsp; Critical threshold exceeded</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with st.container(border=True):
            st.markdown('<p class="dh-center">VOLATILITY GAUGES</p>', unsafe_allow_html=True)
            def _gauge(val):
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
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val,
                    number={"suffix": "%", "font": {"color": _c, "size": 19, "family": "monospace"}},
                    gauge={
                        "axis": {
                            "range": [0, 100],
                            "tickvals": [0, 50, 100],
                            "ticktext": ["LOW", "", "HIGH"],
                            "tickfont": {"color": "#B026FF", "size": 9, "family": "monospace"},
                            "tickwidth": 0,
                            "tickcolor": "rgba(0,0,0,0)",
                        },
                        "bar": {"color": "rgba(0,0,0,0)", "thickness": 0.3},
                        "bgcolor": "#000000", "borderwidth": 0,
                        "steps": _steps,
                        "threshold": {"line": {"color": "#ffffff", "width": 4}, "thickness": 0.88, "value": val},
                    },
                ))
                fig.update_layout(
                    paper_bgcolor="#000000", height=130,
                    margin=dict(t=10, b=10, l=10, r=10),
                    font=dict(family="monospace"),
                )
                return fig
            _tlbl = "color:#B026FF;font-family:monospace;font-size:0.6rem;letter-spacing:0.06em;text-align:center!important;width:100%;display:block;margin:0;"
            _blbl = "color:#B026FF;font-family:monospace;font-size:0.68rem;text-align:center!important;width:100%;display:block;margin:0;"
            st.markdown(f'<p style="{_tlbl}">TSLA — 30D Volatility</p>', unsafe_allow_html=True)
            st.plotly_chart(_gauge(82), use_container_width=True, config={"displayModeBar": False})
            st.markdown(f'<p style="{_blbl}">Extreme &nbsp;·&nbsp; Approaching threshold</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="{_tlbl}">AAPL — 30D Volatility</p>', unsafe_allow_html=True)
            st.plotly_chart(_gauge(67), use_container_width=True, config={"displayModeBar": False})
            st.markdown(f'<p style="{_blbl}">Elevated &nbsp;·&nbsp; Monitor closely</p>', unsafe_allow_html=True)
    st.markdown('<div class="pulse-footer">© 2026 Pulse &nbsp;·&nbsp; All Rights Reserved</div>', unsafe_allow_html=True)
