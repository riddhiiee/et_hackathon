# app.py
import streamlit as st
import streamlit.components.v1 as components
import threading
import time
from dotenv import load_dotenv
from database.db import (init_db, save_user, get_user,
                          get_user_by_email_only, update_user_profile)
from pipelines.consumer_pipeline import consumer_pipeline

load_dotenv()
init_db()

# ── page config ───────────────────────────────────
st.set_page_config(
    page_title="ET ContentFlow",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── hide streamlit UI ─────────────────────────────
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    .block-container {padding: 0 !important;}
    .stApp {background: #0a0a0a;}
    section[data-testid="stSidebar"] {display: none;}

    .stButton > button[kind="primary"] {
        background: #d4a855 !important;
        color: #0a0a0a !important;
        border: none !important;
        border-radius: 0 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
        padding: 16px 40px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #e8c070 !important;
    }
    .stButton > button {
        background: transparent !important;
        color: rgba(240,236,228,0.6) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 0 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 13px !important;
        letter-spacing: 1px !important;
        padding: 6px 10px !important;
    }
    .stButton > button:hover {
        border-color: rgba(255,255,255,0.4) !important;
        color: #f0ece4 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── session state ─────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user" not in st.session_state:
    st.session_state.user = None
if "feed" not in st.session_state:
    st.session_state.feed = []
if "generated" not in st.session_state:
    st.session_state.generated = None
if "selected_article" not in st.session_state:
    st.session_state.selected_article = None
if "otp_email" not in st.session_state:
    st.session_state.otp_email = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False

# ── restore login from URL on refresh ─────────────
params = st.query_params
if st.session_state.user is None and "uid" in params:
    try:
        restored_user = get_user(int(params["uid"]))
        if restored_user:
            st.session_state.user = restored_user
            if st.session_state.page == "landing":
                st.session_state.page = "feed"
    except:
        pass

if st.session_state.user and st.session_state.page == "landing":
    st.session_state.page = "feed"


# ══════════════════════════════════════════════════
# TOP NAV — used on feed, create, profile pages
# ══════════════════════════════════════════════════
def show_top_nav(show_refresh=False):
    from datetime import datetime
    date_str = datetime.now().strftime("%A, %B %d")

    if show_refresh:
        nav_col1, nav_col2, nav_col3 = st.columns([7, 1, 1])
    else:
        nav_col1, nav_col2 = st.columns([9, 1])

    with nav_col1:
        st.markdown(f"""
        <div style="padding: 18px 60px; border-bottom: 1px solid rgba(255,255,255,0.06);
                    display: flex; justify-content: space-between; align-items: center;">
            <div style="font-family:'Playfair Display',serif; font-size:18px;
                        font-weight:700; color:#f0ece4;">
                ET <span style="color:#d4a855;">ContentFlow</span>
            </div>
            <div style="font-family:'DM Sans',sans-serif; font-size:11px;
                        color:rgba(240,236,228,0.4); letter-spacing:2px; text-transform:uppercase;">
                {date_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

    if show_refresh:
        with nav_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("↻ Refresh feed", key="top_refresh_btn", width="stretch"):
                st.session_state.feed = []
                st.rerun()

    last_col = nav_col3 if show_refresh else nav_col2
    with last_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👤", key="profile_nav_btn", width="stretch"):
            st.session_state.page = "profile"
            st.rerun()

# ══════════════════════════════════════════════════
# LANDING PAGE
# ══════════════════════════════════════════════════
def show_landing():
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0a; color: #f0ece4; font-family: 'DM Sans', sans-serif; min-height: 100vh; overflow-x: hidden; }
        .noise { position: fixed; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.03; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E"); pointer-events: none; z-index: 0; }
        .glow { position: fixed; width: 600px; height: 600px; background: radial-gradient(circle, rgba(212,168,85,0.08) 0%, transparent 70%); top: -200px; right: -200px; pointer-events: none; }
        .glow2 { position: fixed; width: 400px; height: 400px; background: radial-gradient(circle, rgba(212,168,85,0.05) 0%, transparent 70%); bottom: -100px; left: -100px; pointer-events: none; }
        nav { position: fixed; top: 0; left: 0; right: 0; padding: 24px 60px; display: flex; justify-content: space-between; align-items: center; z-index: 100; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(10,10,10,0.8); backdrop-filter: blur(20px); }
        .logo { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
        .logo span { color: #d4a855; }
        .nav-tag { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: rgba(240,236,228,0.4); }
        .hero { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 120px 60px 200px; position: relative; z-index: 1; max-width: 720px; }
        .eyebrow { font-size: 11px; letter-spacing: 4px; text-transform: uppercase; color: #d4a855; margin-bottom: 24px; opacity: 0; animation: fadeUp 0.8s ease forwards 0.2s; }
        h1 { font-family: 'Playfair Display', serif; font-size: clamp(52px, 6vw, 88px); font-weight: 900; line-height: 1.0; letter-spacing: -2px; margin-bottom: 32px; opacity: 0; animation: fadeUp 0.8s ease forwards 0.4s; }
        h1 em { font-style: italic; color: #d4a855; }
        .subtitle { font-size: 18px; font-weight: 300; color: rgba(240,236,228,0.6); max-width: 480px; line-height: 1.7; margin-bottom: 56px; opacity: 0; animation: fadeUp 0.8s ease forwards 0.6s; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    </head>
    <body>
    <div class="noise"></div>
    <div class="glow"></div>
    <div class="glow2"></div>
    <nav>
        <div class="logo">ET <span>ContentFlow</span></div>
        <div class="nav-tag">Powered by Economic Times</div>
    </nav>
    <div class="hero">
        <div class="eyebrow">AI-Native News & Content Platform</div>
        <h1>Read. Create.<br><em>Grow.</em></h1>
        <p class="subtitle">Your personalised business intelligence feed — powered by ET's newsroom. Turn any article into content that builds your brand.</p>
    </div>
    </body>
    </html>
    """, height=455, scrolling=False)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("GET STARTED →", width="stretch", type="primary"):
            st.session_state.page = "register"
            st.rerun()
    with col2:
        if st.button("SIGN IN", width="stretch"):
            st.session_state.page = "signin"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="border-top: 1px solid rgba(255,255,255,0.06); display: flex; background: rgba(10,10,10,0.9);">
        <div style="flex:1; padding:24px 40px; border-right:1px solid rgba(255,255,255,0.06);">
            <div style="font-family:'Playfair Display',serif; font-size:28px; font-weight:700; color:#d4a855;">10+</div>
            <div style="font-family:'DM Sans',sans-serif; font-size:11px; color:rgba(240,236,228,0.4); letter-spacing:1px; text-transform:uppercase; margin-top:6px;">Live ET Feeds</div>
        </div>
        <div style="flex:1; padding:24px 40px; border-right:1px solid rgba(255,255,255,0.06);">
            <div style="font-family:'Playfair Display',serif; font-size:28px; font-weight:700; color:#d4a855;">Real-time</div>
            <div style="font-family:'DM Sans',sans-serif; font-size:11px; color:rgba(240,236,228,0.4); letter-spacing:1px; text-transform:uppercase; margin-top:6px;">Personalisation</div>
        </div>
        <div style="flex:1; padding:24px 40px; border-right:1px solid rgba(255,255,255,0.06);">
            <div style="font-family:'Playfair Display',serif; font-size:28px; font-weight:700; color:#d4a855;">4</div>
            <div style="font-family:'DM Sans',sans-serif; font-size:11px; color:rgba(240,236,228,0.4); letter-spacing:1px; text-transform:uppercase; margin-top:6px;">Content Formats</div>
        </div>
        <div style="flex:1; padding:24px 40px;">
            <div style="font-family:'Playfair Display',serif; font-size:28px; font-weight:700; color:#d4a855;">100%</div>
            <div style="font-family:'DM Sans',sans-serif; font-size:11px; color:rgba(240,236,228,0.4); letter-spacing:1px; text-transform:uppercase; margin-top:6px;">ET Verified News</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# SIGN IN — OTP FLOW
# ══════════════════════════════════════════════════
def show_signin():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
    .stApp { background: #0a0a0a; }
    .reg-header { text-align: center; padding: 80px 20px 48px; }
    .reg-eyebrow { font-family: 'DM Sans', sans-serif; font-size: 11px; letter-spacing: 4px; text-transform: uppercase; color: #d4a855; margin-bottom: 16px; }
    .reg-title { font-family: 'Playfair Display', serif; font-size: 48px; font-weight: 700; color: #f0ece4; letter-spacing: -1px; }
    .reg-subtitle { font-family: 'DM Sans', sans-serif; font-size: 16px; color: rgba(240,236,228,0.5); margin-top: 12px; }
    .stTextInput > div > div > input { background: #0a0a0a !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 0 !important; color: #f0ece4 !important; font-family: 'DM Sans', sans-serif !important; padding: 14px 16px !important; font-size: 15px !important; }
    .stTextInput > div > div > input:focus { border-color: #d4a855 !important; box-shadow: none !important; }
    label { color: rgba(240,236,228,0.7) !important; font-family: 'DM Sans', sans-serif !important; font-size: 12px !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
    .stButton > button { background: #d4a855 !important; color: #0a0a0a !important; border: none !important; border-radius: 0 !important; font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important; letter-spacing: 1px !important; text-transform: uppercase !important; padding: 14px !important; width: 100% !important; font-size: 13px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="reg-header">
        <div class="reg-eyebrow">Welcome Back</div>
        <div class="reg-title">Sign In</div>
        <div class="reg-subtitle">We'll send a one-time code to your email.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.otp_sent:
            email = st.text_input("Email Address")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("SEND OTP →"):
                if not email:
                    st.error("Please enter your email")
                else:
                    user = get_user_by_email_only(email.strip())
                    if not user:
                        st.error("No account found. Please register first.")
                    else:
                        from utils.otp import send_otp_email
                        with st.spinner("Sending OTP..."):
                            success = send_otp_email(email.strip())
                        if success:
                            st.session_state.otp_email = email.strip()
                            st.session_state.otp_sent = True
                            st.rerun()
                        else:
                            st.error("Failed to send OTP. Please try again.")
        else:
            st.markdown(f"""
            <div style="text-align:center; font-family:DM Sans; font-size:14px;
                        color:rgba(240,236,228,0.6); margin-bottom:24px;">
                OTP sent to <strong style="color:#d4a855;">{st.session_state.otp_email}</strong>
            </div>
            """, unsafe_allow_html=True)

            otp = st.text_input("Enter 6-digit OTP")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("VERIFY & SIGN IN →"):
                if not otp:
                    st.error("Please enter the OTP")
                else:
                    from utils.otp import verify_otp
                    if verify_otp(st.session_state.otp_email, otp):
                        user = get_user_by_email_only(st.session_state.otp_email)
                        st.session_state.user = user
                        st.session_state.feed = []
                        st.session_state.otp_sent = False
                        st.session_state.otp_email = None
                        st.session_state.page = "feed"
                        st.query_params["uid"] = str(user["id"])
                        st.rerun()
                    else:
                        st.error("Invalid or expired OTP. Please try again.")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Try Different Email"):
                st.session_state.otp_sent = False
                st.session_state.otp_email = None
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Home"):
            st.session_state.otp_sent = False
            st.session_state.otp_email = None
            st.session_state.page = "landing"
            st.rerun()

        st.markdown("""
        <div style="text-align:center; font-family:DM Sans; font-size:13px;
                    color:rgba(240,236,228,0.4); margin-top:24px;">
            New here? Click <strong style="color:#d4a855;">Get Started</strong> to create your profile.
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# REGISTRATION PAGE
# ══════════════════════════════════════════════════
def show_register():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
    .stApp { background: #0a0a0a; }
    .reg-header { text-align: center; padding: 60px 20px 40px; }
    .reg-eyebrow { font-family: 'DM Sans', sans-serif; font-size: 11px; letter-spacing: 4px; text-transform: uppercase; color: #d4a855; margin-bottom: 16px; }
    .reg-title { font-family: 'Playfair Display', serif; font-size: 48px; font-weight: 700; color: #f0ece4; letter-spacing: -1px; }
    .reg-subtitle { font-family: 'DM Sans', sans-serif; font-size: 16px; color: rgba(240,236,228,0.5); margin-top: 12px; }
    .stTextInput > div > div > input { background: #0a0a0a !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 0 !important; color: #f0ece4 !important; font-family: 'DM Sans', sans-serif !important; padding: 14px 16px !important; }
    .stTextInput > div > div > input:focus { border-color: #d4a855 !important; box-shadow: none !important; }
    .stSelectbox > div > div { background: #0a0a0a !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 0 !important; color: #f0ece4 !important; }
    .stMultiSelect > div > div { background: #0a0a0a !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 0 !important; }
    .stMultiSelect span { color: #f0ece4 !important; }
    label { color: rgba(240,236,228,0.7) !important; font-family: 'DM Sans', sans-serif !important; font-size: 12px !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
    .stButton > button { background: #d4a855 !important; color: #0a0a0a !important; border: none !important; border-radius: 0 !important; font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important; letter-spacing: 1px !important; text-transform: uppercase !important; padding: 14px !important; width: 100% !important; font-size: 13px !important; }
    div[data-testid="stCheckbox"] label { text-transform: none !important; font-size: 14px !important; letter-spacing: 0 !important; color: rgba(240,236,228,0.8) !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="reg-header">
        <div class="reg-eyebrow">Create Your Profile</div>
        <div class="reg-title">Build Your Feed</div>
        <div class="reg-subtitle">Takes 60 seconds. Powers everything.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("Your Name")
        email = st.text_input("Email Address")
        profession = st.selectbox("Your Profession", [
            "Finance Analyst", "Investment Banker", "Startup Founder",
            "Student", "Investor / Trader", "Business Executive",
            "Journalist / Writer", "Other"
        ])
        interests = st.multiselect("Topics You Follow", [
            "Markets", "Economy", "Startups", "Wealth & Personal Finance",
            "Banking", "Tech", "Real Estate", "Global Markets"
        ])
        format_pref = st.selectbox("How Do You Like Your News?", [
            "detailed", "quick headlines", "data focused"
        ])
        language = st.selectbox("Preferred Language", [
            "english", "hindi", "both"
        ])
        creator_mode = st.checkbox(
            "I want to create content from news articles", value=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("CREATE MY FEED →"):
            if not name:
                st.error("Please enter your name")
            elif not email:
                st.error("Please enter your email")
            elif not interests:
                st.error("Please select at least one topic")
            else:
                interests_lower = [
                    i.lower().replace(" & personal finance", "").replace(" ", "_")
                    for i in interests
                ]
                user_id = save_user(
                    name=name, profession=profession,
                    interests=interests_lower, format_pref=format_pref,
                    language=language, creator_mode=creator_mode,
                    email=email.strip().lower()
                )
                if user_id is None:
                    st.error("Email already registered. Please sign in instead.")
                else:
                    new_user = get_user(user_id)
                    st.session_state.user = new_user
                    st.session_state.page = "feed"
                    st.query_params["uid"] = str(user_id)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Home"):
            st.session_state.page = "landing"
            st.rerun()


# ══════════════════════════════════════════════════
# PROFILE PAGE
# ══════════════════════════════════════════════════
def show_profile():
    user = st.session_state.user
    show_top_nav()

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
    .stApp { background: #0a0a0a; }
    .profile-header { padding: 40px 60px 32px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 40px; }
    .profile-eyebrow { font-family: 'DM Sans', sans-serif; font-size: 11px; letter-spacing: 4px; text-transform: uppercase; color: #d4a855; margin-bottom: 8px; }
    .profile-name { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700; color: #f0ece4; letter-spacing: -0.5px; }
    .profile-profession { font-family: 'DM Sans', sans-serif; font-size: 13px; color: rgba(240,236,228,0.5); margin-top: 4px; }
    .profile-email { font-family: 'DM Sans', sans-serif; font-size: 13px; color: rgba(240,236,228,0.3); margin-top: 2px; }
    .section-label { font-family: 'DM Sans', sans-serif; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: rgba(240,236,228,0.4); margin-bottom: 16px; margin-top: 32px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .stSelectbox > div > div { background: #0a0a0a !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 0 !important; color: #f0ece4 !important; }
    .stMultiSelect > div > div { background: #0a0a0a !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 0 !important; }
    .stMultiSelect span { color: #f0ece4 !important; }
    label { color: rgba(240,236,228,0.7) !important; font-family: 'DM Sans', sans-serif !important; font-size: 12px !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
    .stButton > button { border-radius: 0 !important; font-family: 'DM Sans', sans-serif !important; font-size: 11px !important; letter-spacing: 1px !important;}
    div[data-testid="stCheckbox"] label { text-transform: none !important; font-size: 14px !important; letter-spacing: 0 !important; color: rgba(240,236,228,0.8) !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="profile-header">
        <div class="profile-eyebrow">Your Profile</div>
        <div class="profile-name">{user['name']}</div>
        <div class="profile-profession">{user['profession']}</div>
        <div class="profile-email">{user.get('email', '')}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Feed", width="stretch"):
            st.session_state.page = "feed"
            st.rerun()

        st.markdown('<div class="section-label">Update Your Preferences</div>',
                    unsafe_allow_html=True)

        interest_map = {
            "markets": "Markets", "economy": "Economy",
            "startups": "Startups", "wealth": "Wealth & Personal Finance",
            "banking": "Banking", "tech": "Tech",
            "real_estate": "Real Estate", "global_markets": "Global Markets"
        }
        current_interests_display = [
            interest_map.get(i, i.replace("_", " ").title())
            for i in user["interests"]
        ]

        profession_options = [
            "Finance Analyst", "Investment Banker", "Startup Founder",
            "Student", "Investor / Trader", "Business Executive",
            "Journalist / Writer", "Other"
        ]
        profession = st.selectbox(
            "Profession", profession_options,
            index=profession_options.index(user["profession"])
            if user["profession"] in profession_options else 0
        )

        interests = st.multiselect("Topics You Follow", [
            "Markets", "Economy", "Startups", "Wealth & Personal Finance",
            "Banking", "Tech", "Real Estate", "Global Markets"
        ], default=current_interests_display)

        format_options = ["detailed", "quick headlines", "data focused"]
        format_pref = st.selectbox(
            "News Format", format_options,
            index=format_options.index(user["format_preference"])
            if user["format_preference"] in format_options else 0
        )

        language_options = ["english", "hindi", "both"]
        language = st.selectbox(
            "Preferred Language", language_options,
            index=language_options.index(user["language"])
            if user["language"] in language_options else 0
        )

        creator_mode = st.checkbox(
            "I want to create content from news articles",
            value=user.get("creator_mode", True)
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("SAVE CHANGES →", width="stretch", type="primary"):
            interests_lower = [
                i.lower().replace(" & personal finance", "").replace(" ", "_")
                for i in interests
            ]
            update_user_profile(
                user_id=user["id"], profession=profession,
                interests=interests_lower, format_pref=format_pref,
                language=language, creator_mode=creator_mode
            )
            updated_user = get_user(user["id"])
            st.session_state.user = updated_user
            st.session_state.feed = []
            st.success("Profile updated! Feed will refresh with new preferences.")
            time.sleep(1.5)
            st.session_state.page = "feed"
            st.rerun()

        st.markdown('<div class="section-label">Account</div>',
                    unsafe_allow_html=True)

        if st.button("LOGOUT", width="stretch"):
            st.session_state.user = None
            st.session_state.feed = []
            st.session_state.page = "landing"
            st.query_params.clear()
            st.rerun()


# ══════════════════════════════════════════════════
# LOADING SCREEN
# ══════════════════════════════════════════════════
def show_loading_screen(placeholder, msg_index):
    messages = [
        ("SOURCING", "Pulling live stories from ET's newsroom"),
        ("ANALYSING", "Reading today's market signals and headlines"),
        ("FILTERING", "Matching stories to your professional profile"),
        ("DID YOU KNOW", "The Economic Times reaches over 800 million readers globally"),
        ("RANKING", "Scoring each article for relevance to your interests"),
        ("DID YOU KNOW", "India has the world's largest number of listed companies on BSE"),
        ("CURATING", "Assembling your personalised intelligence brief"),
        ("DID YOU KNOW", "ET Markets tracks over 5,000 stocks across NSE and BSE in real time"),
        ("FINALISING", "Your briefing is almost ready"),
    ]
    msg = messages[msg_index % len(messages)]
    tag = msg[0]
    text = msg[1]
    progress = min(int((msg_index / len(messages)) * 100), 95)

    placeholder.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
    .loading-wrap {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: #0a0a0a; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }}
    .loading-logo {{ font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #f0ece4; margin-bottom: 80px; opacity: 0.5; }}
    .loading-logo span {{ color: #d4a855; }}
    .loading-tag {{ font-family: 'DM Sans', sans-serif; font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: #d4a855; margin-bottom: 16px; }}
    .loading-text {{ font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; color: #f0ece4; text-align: center; max-width: 480px; line-height: 1.3; margin-bottom: 64px; }}
    .loading-bar-wrap {{ width: 280px; height: 1px; background: rgba(255,255,255,0.08); }}
    .loading-bar-fill {{ height: 100%; background: #d4a855; width: {progress}%; transition: width 1.8s ease; }}
    .loading-percent {{ font-family: 'DM Sans', sans-serif; font-size: 11px; color: rgba(240,236,228,0.25); letter-spacing: 2px; margin-top: 14px; text-align: center; }}
    </style>
    <div class="loading-wrap">
        <div class="loading-logo">ET <span>ContentFlow</span></div>
        <div class="loading-tag">{tag}</div>
        <div class="loading-text">{text}</div>
        <div class="loading-bar-wrap"><div class="loading-bar-fill"></div></div>
        <div class="loading-percent">{progress}%</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# FEED PAGE
# ══════════════════════════════════════════════════
def show_feed():
    user = st.session_state.user

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
    .stApp { background: #0a0a0a; }
    .feed-header { padding: 32px 60px 28px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 32px; }
    .feed-greeting { font-family: 'DM Sans', sans-serif; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: #d4a855; margin-bottom: 6px; }
    .feed-title { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 700; color: #f0ece4; letter-spacing: -0.5px; }
    .feed-body { padding: 0 60px; }
    .article-card { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); padding: 24px; margin-bottom: 16px; transition: all 0.3s ease; position: relative; overflow: hidden; }
    .article-card:hover { background: rgba(212,168,85,0.04); border-color: rgba(212,168,85,0.2); }
    .article-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px; background: #d4a855; opacity: 0; transition: opacity 0.3s ease; }
    .article-card:hover::before { opacity: 1; }
    .article-meta-row { display: flex; gap: 12px; align-items: center; margin-bottom: 10px; }
    .topic-tag { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #d4a855; font-family: 'DM Sans', sans-serif; }
    .score-tag { font-size: 10px; color: rgba(240,236,228,0.3); font-family: 'DM Sans', sans-serif; }
    .article-title { font-family: 'Playfair Display', serif; font-size: 19px; font-weight: 700; color: #f0ece4; line-height: 1.3; margin-bottom: 10px; letter-spacing: -0.3px; }
    .article-summary { font-family: 'DM Sans', sans-serif; font-size: 13px; color: rgba(240,236,228,0.6); line-height: 1.7; margin-bottom: 14px; }
    .why-relevant { font-family: 'DM Sans', sans-serif; font-size: 12px; color: rgba(212,168,85,0.8); font-style: italic; padding: 8px 12px; border-left: 2px solid rgba(212,168,85,0.3); background: rgba(212,168,85,0.04); margin-bottom: 16px; line-height: 1.5; }
    .article-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .stButton > button { border-radius: 0 !important; font-family: 'DM Sans', sans-serif !important; font-size: 10px !important; letter-spacing: 1px !important; text-transform: uppercase !important; padding: 8px 12px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── top nav with refresh ──────────────────────
    show_top_nav(show_refresh=True)

    # ── feed header ───────────────────────────────
    st.markdown(f"""
    <div class="feed-header">
        <div class="feed-greeting">Good morning, {user['name']}</div>
        <div class="feed-title">Your ET Briefing</div>
    </div>
    """, unsafe_allow_html=True)

    # ── load feed ─────────────────────────────────
    if not st.session_state.feed:
        placeholder = st.empty()
        feed_result = [None]
        error_result = [None]

        def run_pipeline():
            try:
                initial_state = {
                    "user_profile": user,
                    "raw_articles": [], "enriched_articles": [],
                    "personalized_feed": [], "selected_article": None,
                    "generated_content": None, "tone_adapted_content": None,
                    "compliance_passed": None, "compliance_issues": None,
                    "final_content": None, "retry_count": 0,
                    "performance_history": None, "content_strategy": None
                }
                result = consumer_pipeline.invoke(initial_state)
                feed_result[0] = result["personalized_feed"]
            except Exception as e:
                error_result[0] = str(e)

        thread = threading.Thread(target=run_pipeline)
        thread.start()

        msg_index = 0
        while thread.is_alive():
            show_loading_screen(placeholder, msg_index)
            msg_index += 1
            time.sleep(2)

        thread.join()
        placeholder.empty()

        if error_result[0]:
            st.error(f"Error: {error_result[0]}")
            return

        st.session_state.feed = feed_result[0]

        def run_strategist_silent():
            try:
                from pipelines.strategy_pipeline import strategist_pipeline
                silent_state = {
                    "user_profile": user,
                    "raw_articles": [], "enriched_articles": [],
                    "personalized_feed": [], "selected_article": None,
                    "generated_content": None, "tone_adapted_content": None,
                    "compliance_passed": None, "compliance_issues": None,
                    "final_content": None, "retry_count": 0,
                    "performance_history": None, "content_strategy": None
                }
                strategist_pipeline.invoke(silent_state)
            except Exception as e:
                print(f"Strategist error: {e}")

        bg = threading.Thread(target=run_strategist_silent, daemon=True)
        bg.start()
        st.rerun()

    # ── display feed ──────────────────────────────
    feed = st.session_state.feed
    if not feed:
        st.warning("No articles found. Try refreshing.")
        return

    primary = [a for a in feed if (a.get("relevance_score") or 0) >= 5]
    secondary = [a for a in feed if (a.get("relevance_score") or 0) < 5]

    st.markdown('<div class="feed-body">', unsafe_allow_html=True)

    def render_article(article, i):
        score = article.get("relevance_score", 0)
        topic = article.get("topic", "").upper().replace("_", " ")
        title = article.get("title", "")
        summary = article.get("personalized_summary", article.get("summary", ""))
        summary = summary.strip()
        if len(summary) > 300:
            summary = summary[:300].rsplit(" ", 1)[0] + "..."
        why = article.get("why_relevant", "")
        image = article.get("image_url", "")
        url = article.get("article_url", "#")

        # left: article text | right: image
        col_text, col_img = st.columns([3, 1])

        with col_text:
            st.markdown(f"""
            <div class="article-card">
                <div class="article-meta-row">
                    <span class="topic-tag">{topic}</span>
                    <span class="score-tag">{score}/10 match</span>
                </div>
                <div class="article-title">{title}</div>
                <div class="article-summary">{summary}</div>
                {f'<div class="why-relevant">{why}</div>' if why else ''}
            </div>
            """, unsafe_allow_html=True)

            # ── horizontal action buttons ─────────
            btn_cols = st.columns(4) if user.get("creator_mode") else st.columns(3)

            with btn_cols[0]:
                st.markdown(f"""
                <a href="{url}" target="_blank" style="
                    display: block;
                    background: #d4a855;
                    color: #0a0a0a;
                    text-align: center;
                    padding: 8px 12px;
                    font-family: DM Sans, sans-serif;
                    font-size: 18px;
                    text-decoration: none;
                    font-weight: 500;
                ">Read Article ↗</a>
                """, unsafe_allow_html=True)

            with btn_cols[1]:
                if st.button("Mark Read", key=f"read_{i}", width="stretch"):
                    from database.db import log_interaction
                    log_interaction(user_id=user["id"],
                                    article_id=article.get("id") or i,
                                    action="read_full", time_spent=120,
                                    topic=article.get("topic", "general"))
                    st.success("Noted")

            with btn_cols[2]:
                if st.button("Not Interested", key=f"skip_{i}", width="stretch"):
                    from database.db import log_interaction
                    log_interaction(user_id=user["id"],
                                    article_id=article.get("id") or i,
                                    action="skipped", time_spent=0,
                                    topic=article.get("topic", "general"))
                    st.rerun()

            if user.get("creator_mode"):
                with btn_cols[3]:
                    if st.button("Create Content", key=f"create_{i}", width="stretch"):
                        from database.db import log_interaction
                        log_interaction(user_id=user["id"],
                                        article_id=article.get("id") or i,
                                        action="created_content", time_spent=0,
                                        topic=article.get("topic", "general"))
                        st.session_state.selected_article = article
                        st.session_state.generated = None
                        st.session_state.page = "create"
                        st.rerun()

        with col_img:
            if image:
                st.image(image, width="stretch")

        st.markdown("---")

    for i, article in enumerate(primary[:6]):
        render_article(article, i)

    if secondary:
        st.markdown("""
        <div style="margin: 48px 0 36px; position: relative; height: 28px;
                    display: flex; align-items: center; justify-content: center;">
            <div style="position: absolute; left: 0; right: 0; top: 50%;
                        height: 1px; background: rgba(255,255,255,1);"></div>
            <span style="position: relative; background: #0a0a0a; padding: 0 20px;
                         font-family: 'DM Sans', sans-serif; font-size: 10px;
                         letter-spacing: 3px; text-transform: uppercase;
                         color: rgba(255,255,255,0.35); white-space: nowrap;">
                Not Based on Your Interests — Explore More
            </span>
        </div>
        """, unsafe_allow_html=True)
        for i, article in enumerate(secondary[:3]):
            render_article(article, i + 100)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# CREATE PAGE
# ══════════════════════════════════════════════════
def show_create():
    user = st.session_state.user
    article = st.session_state.get("selected_article")

    if not article:
        st.session_state.page = "feed"
        st.rerun()

    show_top_nav()

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
    .stApp { background: #0a0a0a; }

    .create-header {
        padding: 24px 20px 20px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 24px;
    }
    .back-link {
        font-family: 'DM Sans', sans-serif;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(240,236,228,0.4);
        margin-bottom: 12px;
        cursor: pointer;
    }
    .create-eyebrow {
        font-family: 'DM Sans', sans-serif;
        font-size: 11px;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #d4a855;
        margin-bottom: 6px;
    }
    .create-title {
        font-family: 'Playfair Display', serif;
        font-size: 28px;
        font-weight: 700;
        color: #f0ece4;
        letter-spacing: -0.5px;
    }
    .source-card {
        background: rgba(212,168,85,0.05);
        border: 1px solid rgba(212,168,85,0.2);
        border-left: 3px solid #d4a855;
        padding: 12px 16px;
        margin-bottom: 24px;
    }
    .source-label {
        font-size: 9px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #d4a855;
        margin-bottom: 4px;
        font-family: 'DM Sans', sans-serif;
    }
    .source-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 15px;
        color: rgba(240,236,228,0.8);
        line-height: 1.4;
    }
    .platform-name {
        font-family: 'DM Sans', sans-serif;
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #d4a855;
        margin-bottom: 10px;
    }
    .stButton > button {
        border-radius: 0 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 11px !important;
        letter-spacing: 1px !important;
    }
    .stTextArea > div > div > textarea {
        background: #1a1a1a !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 0 !important;
        color: #f0ece4 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.7 !important;
    }
    /* tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 11px !important;
        letter-spacing: 2px !important;
        color: rgba(240,236,228,0.4) !important;
    }
    .stTabs [aria-selected="true"] {
        color: #d4a855 !important;
        border-bottom: 2px solid #d4a855 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── back button ───────────────────────────────
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back", key="back_to_feed"):
            st.session_state.page = "feed"
            st.session_state.generated = None
            st.rerun()

    # ── header ────────────────────────────────────
    st.markdown(f"""
    <div class="create-header">
        <div class="create-eyebrow">Creator Studio</div>
        <div class="create-title">Generate Content</div>
    </div>
    """, unsafe_allow_html=True)

    # ── source article ────────────────────────────
    _, center, _ = st.columns([1, 6, 1])
    st.markdown(f"""
    <div class="source-card">
        <div class="source-label">Source Article</div>
        <div class="source-title">{article['title']}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── generate ──────────────────────────────────
    if not st.session_state.generated:
        with st.spinner("Generating content..."):
            #── REAL PIPELINE (uncomment when API resets) ──
            try:
                from pipelines.creator_pipeline import creator_pipeline
                creator_state = {
                    "user_profile": user, "raw_articles": [], "enriched_articles": [],
                    "personalized_feed": [], "selected_article": article,
                    "generated_content": None, "tone_adapted_content": None,
                    "compliance_passed": None, "compliance_issues": None,
                    "final_content": None, "retry_count": 0,
                    "performance_history": None, "content_strategy": None
                }
                creator_result = creator_pipeline.invoke(creator_state)
                st.session_state.generated = creator_result["final_content"]
                st.rerun()
            except Exception as e:
                st.error("API limit reached. Please wait a few minutes.")
                st.session_state.page = "feed"
                st.rerun()    

    final = st.session_state.generated
    if not final:
        st.error("Content generation failed. Please try again.")
        return

    # ── accuracy badge ────────────────────────────
    _, center, _ = st.columns([1, 6, 1])
    with center:
        accuracy = final.get("accuracy_score", 0)
        st.markdown(f"""
        <div style="margin-bottom:20px;">
            <span style="background:rgba(34,197,94,0.1);
                         border:1px solid rgba(34,197,94,0.3);
                         color:#22c55e; padding:5px 12px;
                         font-size:10px; letter-spacing:2px;
                         font-family:DM Sans,sans-serif;
                         text-transform:uppercase;">
                Fact Checked — {accuracy}% Accuracy
            </span>
        </div>
        """, unsafe_allow_html=True)

    # ── content tabs ──────────────────────────────
    _, center, _ = st.columns([1, 6, 1])
    with center:
        # regenerate button top right
        btn_col1, btn_col2 = st.columns([5, 1])
        with btn_col2:
            if st.button("↻ Regenerate", key="regen", width="stretch"):
                st.session_state.generated = None
                st.rerun()

        tab1, tab2, tab3, tab4 = st.tabs([
            "LinkedIn", "Twitter / X", "Instagram", "Video Script"
        ])

        with tab1:
            st.markdown('<div class="platform-name">LinkedIn Post</div>',
                        unsafe_allow_html=True)
            linkedin_content = st.text_area(
                "linkedin", value=final.get("linkedin", ""),
                height=260, key="linkedin_edit", label_visibility="collapsed"
            )
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("Copy Post", key="copy_li", width="stretch"):
                    st.code(linkedin_content)
                    st.success("Copy the text above")
            with col2:
                st.markdown(
                    f'<div style="text-align:right; padding:10px 0; color:rgba(240,236,228,0.4); font-family:DM Sans; font-size:11px;">{len(linkedin_content)} chars</div>',
                    unsafe_allow_html=True
                )

        with tab2:
            st.markdown('<div class="platform-name">Twitter / X Thread</div>',
                        unsafe_allow_html=True)
            tweets = final.get("twitter", [])
            for i, tweet in enumerate(tweets):
                edited = st.text_area(
                    f"Tweet {i+1}", value=tweet,
                    height=90, key=f"tweet_{i}"
                )
                char_count = len(edited)
                color = "#22c55e" if char_count <= 280 else "#ef4444"
                st.markdown(
                    f'<div style="text-align:right; color:{color}; font-size:11px; font-family:DM Sans; margin-bottom:10px;">{char_count}/280</div>',
                    unsafe_allow_html=True
                )

        with tab3:
            st.markdown('<div class="platform-name">Instagram Caption</div>',
                        unsafe_allow_html=True)
            insta_content = st.text_area(
                "instagram", value=final.get("instagram", ""),
                height=220, key="instagram_edit", label_visibility="collapsed"
            )
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("Copy Caption", key="copy_ig", width="stretch"):
                    st.code(insta_content)
                    st.success("Copy the text above")
            with col2:
                st.markdown(
                    f'<div style="text-align:right; padding:10px 0; color:rgba(240,236,228,0.4); font-family:DM Sans; font-size:11px;">{len(insta_content)} chars</div>',
                    unsafe_allow_html=True
                )

        with tab4:
            st.markdown('<div class="platform-name">Video Script — 60 seconds</div>',
                        unsafe_allow_html=True)
            script_content = st.text_area(
                "script", value=final.get("video_script", ""),
                height=340, key="script_edit", label_visibility="collapsed"
            )
            if st.button("Copy Script", key="copy_sc", width="stretch"):
                st.code(script_content)
                st.success("Copy the text above")

# ══════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════
def main():
    if st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "register":
        show_register()
    elif st.session_state.page == "signin":
        show_signin()
    elif st.session_state.page == "profile":
        if st.session_state.user:
            show_profile()
        else:
            st.session_state.page = "landing"
            st.rerun()
    elif st.session_state.page == "feed":
        if st.session_state.user:
            show_feed()
        else:
            st.session_state.page = "landing"
            st.rerun()
    elif st.session_state.page == "create":
        if st.session_state.user:
            show_create()
        else:
            st.session_state.page = "landing"
            st.rerun()

if __name__ == "__main__":
    main()