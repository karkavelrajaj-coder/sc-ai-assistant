"""SC First Bank – AI voice assistant POC (Streamlit).

Client view:  https://<app>.streamlit.app            (simple call screen, nothing technical)
Team view:    https://<app>.streamlit.app/?admin=1   (adds settings + diagnostics; needs ADMIN_PASSCODE)
Secrets:      OPENAI_API_KEY (required), DEMO_PASSCODE, ADMIN_PASSCODE, optional VOICE / REALTIME_MODEL / LANGUAGE
"""
import json
import os
import time
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

from prompts import RESULT_LABELS, RESULT_TOOL, build_instructions

ROOT = Path(__file__).parent
PKG = json.loads((ROOT / "data" / "call_package.json").read_text(encoding="utf-8"))
TEMPLATE = (ROOT / "voice_component.html").read_text(encoding="utf-8")

# Vocabulary hints so the live captions spell bank terms correctly
TRANSCRIBE_HINTS = {
    "ko": "SC제일은행 강남 WM센터 상담. 박서연 고객님, 김지은 RM, 정기예금, 만기, 재예치, 달러 자산, 지점 방문, 생년월일 육이공삼일오, 아직 못 정했어요, 상담 받고 싶어요.",
    "en": "SC First Bank call. Ms. Park Seo-yeon, RM Kim Ji-eun, time deposit, maturity, renewal, USD assets, branch visit, undecided, I'd like to talk to my RM, six two zero three one five.",
}
MODELS = ["gpt-realtime-2.1", "gpt-realtime-2.1-mini", "gpt-realtime-2"]
VOICES = ["marin", "cedar", "coral", "shimmer", "sage", "alloy", "ash", "ballad", "echo", "verse"]


def secret(name, default=""):
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name, default)


API_KEY = secret("OPENAI_API_KEY")
API_BASE = secret("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
DEMO_PASSCODE = secret("DEMO_PASSCODE")
ADMIN_PASSCODE = secret("ADMIN_PASSCODE")

want_admin = st.query_params.get("admin") == "1"

st.set_page_config(
    page_title="SC제일은행 AI 상담 도우미",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide all platform chrome for a clean, product-like screen
hide_sidebar = '[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:none !important;}'
st.markdown(
    f"""<style>
    #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    .stDeployButton, [data-testid="stAppDeployButton"], .viewerBadge_container__1QSob, [class*="viewerBadge"] {{display:none !important;}}
    {hide_sidebar}
    .block-container{{padding-top:1.6rem;padding-bottom:.5rem;max-width:1180px}}
    .top{{display:flex;align-items:center;justify-content:space-between;margin:0 4px 14px}}
    .logo{{font-weight:800;font-size:1.3rem;color:#0b2545;letter-spacing:.2px}}
    .logo span{{color:#0f8b8d}}
    .tagline{{color:#6b7385;font-size:.9rem}}
    .gate{{max-width:380px;margin:12vh auto 0;text-align:center}}
    .gate h2{{color:#0b2545;margin-bottom:.2rem}}
    .gate p{{color:#6b7385}}
    </style>""",
    unsafe_allow_html=True,
)

# ---------------- Access ----------------
if DEMO_PASSCODE and not st.session_state.get("authed"):
    st.markdown('<div class="gate"><h2>📞 SC제일은행</h2><p>AI 상담 도우미 · AI Voice Assistant</p></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        code = st.text_input("Access code", type="password", label_visibility="collapsed", placeholder="Access code")
        if code:
            if code == DEMO_PASSCODE or (ADMIN_PASSCODE and code == ADMIN_PASSCODE):
                st.session_state.authed = True
                st.session_state.is_admin = bool(ADMIN_PASSCODE and code == ADMIN_PASSCODE)
                st.rerun()
            else:
                st.error("코드가 올바르지 않습니다 · Incorrect code")
    st.stop()

# Admin = ?admin=1 AND (admin passcode used, or no admin passcode configured — local runs)
is_admin = want_admin and (st.session_state.get("is_admin") or not ADMIN_PASSCODE)

# ---------------- Settings (team only) ----------------
lang = secret("LANGUAGE", "ko") if secret("LANGUAGE", "ko") in ("ko", "en") else "ko"
voice = secret("VOICE", "marin")
model = secret("REALTIME_MODEL", MODELS[0])
silence_ms = 450
if is_admin:
    # Team settings live on the page (not in the sidebar) so they are always reachable
    with st.expander("⚙️ Team settings (only visible in team mode)", expanded=False):
        c1, c2, c3, c4 = st.columns([1.2, 1, 1.2, 1.4])
        lang = "ko" if c1.radio("Language", ["Korean", "English (rehearsal)"], index=0 if lang == "ko" else 1, horizontal=True) == "Korean" else "en"
        voice = c2.selectbox("Voice", VOICES, index=VOICES.index(voice) if voice in VOICES else 0)
        model = c3.selectbox("Model", MODELS, index=MODELS.index(model) if model in MODELS else 0)
        silence_ms = c4.slider("Reply after silence (ms)", 250, 1000, silence_ms, 50)
        b1, b2 = st.columns([1, 3])
        if b1.button("New session", use_container_width=True):
            st.session_state.pop("token", None)
        b2.caption("Changing a setting resets the call screen. Clients never see this panel.")


# ---------------- Session key (server-side; the API key never reaches the browser) ----------------
def mint_token(lang, voice, model, silence_ms):
    body = {
        "expires_after": {"anchor": "created_at", "seconds": 1800},
        "session": {
            "type": "realtime",
            "model": model,
            "instructions": build_instructions(PKG, lang),
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "noise_reduction": {"type": "near_field"},
                    "transcription": {"model": "gpt-4o-transcribe", "language": lang, "prompt": TRANSCRIBE_HINTS[lang]},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": int(silence_ms),
                        "create_response": True,
                        "interrupt_response": True,
                    },
                },
                "output": {"voice": voice},
            },
            "tools": [RESULT_TOOL],
            "tool_choice": "auto",
        },
    }
    r = requests.post(
        f"{API_BASE}/v1/realtime/client_secrets",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=body,
        timeout=20,
    )
    if r.status_code >= 400:
        try:
            msg = r.json().get("error", {}).get("message", r.text)
        except Exception:
            msg = r.text
        raise RuntimeError(f"{r.status_code}: {msg[:300]}")
    j = r.json()
    return {"value": j["value"], "expires_at": j.get("expires_at", time.time() + 1800)}


settings_key = (lang, voice, model, silence_ms)
token, token_error = "", ""
if not API_KEY:
    token_error = "OPENAI_API_KEY missing in secrets"
else:
    cached = st.session_state.get("token")
    if cached and cached["key"] == settings_key and cached["expires_at"] - time.time() > 120:
        token = cached["value"]
    else:
        try:
            t = mint_token(*settings_key)
            st.session_state.token = {**t, "key": settings_key}
            token = t["value"]
        except Exception as e:  # noqa: BLE001
            token_error = str(e)

# ---------------- Page ----------------
st.markdown(
    '<div class="top"><div class="logo">SC제일은행 <span>AI 상담 도우미</span></div>'
    '<div class="tagline">AI Voice Assistant</div></div>',
    unsafe_allow_html=True,
)
if is_admin and token_error:
    st.error(f"Session error: {token_error}")

config = {
    "token": token,
    "token_error": token_error if is_admin else "",
    "rtc_url": f"{API_BASE}/v1/realtime/calls",
    "admin": bool(is_admin),
    "lang": lang,
    "call_id": PKG["call_id"],
    "customer_id": PKG["customer"]["customer_id"],
    "script_id": PKG["script_id"],
    "slots": [{"id": s["id"], "short": s["short"], "ko": s["ko"]} for s in PKG["slots"]],
    "labels": RESULT_LABELS,
}
components.html(TEMPLATE.replace("__CONFIG__", json.dumps(config, ensure_ascii=False).replace("</", "<\\/")), height=710, scrolling=False)
