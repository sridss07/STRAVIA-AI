import os
import json
import random
import time
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.risk_prediction import RiskPredictor
from src.alternative_suppliers import AlternativeSupplierAnalyzer
from src.translations import SUPPORTED_LANGUAGES, t
from src.assistant import StraviaAssistant
from src.report_generator import ExecutiveReportGenerator
from src.auth import AuthManager
from src.subscriptions import SubscriptionManager, PLANS
auth_mgr = AuthManager()
sub_mgr = SubscriptionManager()
st.set_page_config(
    page_title="STRAVIA AI - Supply Chain Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #F4FAFA;
        background-image: 
            radial-gradient(at 8% 8%, rgba(45, 212, 191, 0.14) 0px, transparent 520px),
            radial-gradient(at 92% 86%, rgba(56, 189, 248, 0.12) 0px, transparent 560px),
            url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1400' height='900' viewBox='0 0 1400 900'><g fill='none' stroke='%2394A3B8' stroke-width='1' opacity='0.15'><!-- Global Trade Route Arcs --><path d='M150,250 Q400,120 680,220 T1200,280' stroke='%230EA5E9' stroke-width='1.5' stroke-dasharray='6,6' opacity='0.35'/><path d='M220,550 Q520,320 880,380 T1280,480' stroke='%230284C7' stroke-width='1.5' stroke-dasharray='5,5' opacity='0.3'/><path d='M680,220 Q820,480 980,580' stroke='%230EA5E9' stroke-width='1.2' stroke-dasharray='4,4' opacity='0.25'/><path d='M350,680 Q650,580 980,580' stroke='%2338BDF8' stroke-width='1' stroke-dasharray='6,6' opacity='0.25'/><!-- Trade Hub Data Nodes --><circle cx='150' cy='250' r='5' fill='%230EA5E9' opacity='0.5'/><circle cx='680' cy='220' r='6' fill='%230284C7' opacity='0.6'/><circle cx='1200' cy='280' r='5' fill='%230EA5E9' opacity='0.5'/><circle cx='220' cy='550' r='5' fill='%230284C7' opacity='0.4'/><circle cx='880' cy='380' r='6' fill='%230EA5E9' opacity='0.5'/><circle cx='980' cy='580' r='5' fill='%230284C7' opacity='0.5'/><circle cx='350' cy='680' r='4' fill='%2338BDF8' opacity='0.4'/><!-- AI Grid & Network Lattice --><g opacity='0.18' fill='%2364748B'><circle cx='280' cy='160' r='1.5'/><circle cx='460' cy='190' r='1.5'/><circle cx='820' cy='150' r='1.5'/><circle cx='1050' cy='210' r='1.5'/><circle cx='400' cy='440' r='1.5'/><circle cx='620' cy='500' r='1.5'/><circle cx='1120' cy='450' r='1.5'/><circle cx='520' cy='720' r='1.5'/></g><!-- Supply Chain Hexagonal Logistics Hubs --><polygon points='680,210 690,215 690,225 680,230 670,225 670,215' stroke='%230EA5E9' stroke-width='1.2' opacity='0.4'/><polygon points='880,370 890,375 890,385 880,390 870,385 870,375' stroke='%230284C7' stroke-width='1.2' opacity='0.4'/><polygon points='220,540 230,545 230,555 220,560 210,555 210,545' stroke='%2338BDF8' stroke-width='1.2' opacity='0.35'/></g></svg>");
        background-repeat: no-repeat;
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;
    }
    .main {
        background: transparent;
        color: #212529;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    [data-testid="stMainBlockContainer"] {
        position: relative;
        max-width: 1480px;
        padding-top: 2.25rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMainBlockContainer"]::before {
        content: "";
        position: absolute;
        inset: 0.75rem 0.5rem 1.25rem;
        z-index: -1;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 28px;
        background-color: rgba(255, 255, 255, 0.68);
        background-image: linear-gradient(rgba(15, 118, 110, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(15, 118, 110, 0.035) 1px, transparent 1px);
        background-size: 32px 32px;
        box-shadow: 0 22px 70px rgba(15, 118, 110, 0.08);
        backdrop-filter: blur(6px);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(239, 250, 248, 0.96) 0%, rgba(247, 251, 255, 0.96) 100%);
        border-right: 1px solid rgba(15, 118, 110, 0.12);
    }
    [data-testid="stSidebar"] > div:first-child {
        background-image: radial-gradient(circle at 18% 12%, rgba(45, 212, 191, 0.13) 0 2px, transparent 2.5px), radial-gradient(circle at 82% 34%, rgba(56, 189, 248, 0.10) 0 2px, transparent 2.5px);
        background-size: 42px 42px, 58px 58px;
    }
    .stAppHeader {
        background-color: #FFFFFF;
    }
    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E9ECEF;
        border-top: 3px solid #0F766E;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        text-align: center;
        min-height: 125px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 13px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .risk-badge-low {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .risk-badge-medium {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .risk-badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .summary-box {
        background: rgba(236, 253, 245, 0.95);
        border-left: 5px solid #0F766E;
        padding: 18px;
        border-radius: 6px;
        margin-top: 15px;
        color: #1E3A8A;
        box-shadow: 0 4px 12px rgba(18, 59, 58, 0.05);
    }
    .assistant-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }
    .radar-card {
        background-color: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .user-profile-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 15px;
    }
    .plan-badge-free {
        background-color: #E2E8F0;
        color: #475569;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }
    .plan-badge-pro {
        background-color: #0F766E;
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }
    .plan-badge-enterprise {
        background-color: #1E3A8A;
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }
    .auth-shell {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 24px;
        padding: 28px 30px 24px;
        box-shadow: 0 20px 55px rgba(15, 118, 110, 0.10);
        backdrop-filter: blur(10px);
    }
    .auth-illustration {
        background: linear-gradient(145deg, #E7F8F5 0%, #EFF8FF 100%);
        border: 1px solid #D5EEE9;
        border-radius: 24px;
        padding: 14px 18px 8px;
        box-shadow: 0 20px 55px rgba(14, 116, 144, 0.09);
        overflow: hidden;
    }
    .auth-kicker {
        color: #0F766E;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        margin: 0 0 4px;
    }
    .auth-caption {
        color: #475569;
        font-size: 14px;
        line-height: 1.55;
        margin: 0 0 6px;
    }
</style>
""", unsafe_allow_html=True)
@st.cache_data
def load_dataset():
    data_path = os.path.join(os.path.dirname(__file__), "data", "processed", "integrated_dataset.csv")
    if not os.path.exists(data_path):
        st.error(f"Integrated dataset not found at {data_path}. Please run data_integration.py first.")
        st.stop()
    return pd.read_csv(data_path)
@st.cache_data
def load_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), "models", "model_metrics.json")
    if not os.path.exists(metrics_path):
        return {}
    with open(metrics_path, "r") as f:
        return json.load(f)
def render_locked_feature_card(feature_title: str, feature_desc: str):
    """Renders a styled authorization wall card for locked Pro/Enterprise features."""
    st.markdown(f"""
    <div style="background-color: #FFFBEB; border: 2px dashed #F59E0B; padding: 25px; border-radius: 12px; text-align: center; margin: 20px 0;">
        <h3 style="color: #92400E; margin: 0 0 10px 0;">{t('locked_feature_title')} — {feature_title}</h3>
        <p style="color: #78350F; font-size: 15px; margin-bottom: 20px;">{feature_desc}</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"⚡ {t('btn_upgrade_pro')}", key=f"upgrade_{feature_title}", use_container_width=True):
        st.session_state["show_demo_payment"] = True
        st.rerun()
def render_pricing_page(user_plan: str):
    """Renders the public & authenticated pricing page with demo payment upgrade trigger."""
    st.markdown(f"## 💳 {t('pricing_header')}")
    st.markdown(f"*{t('pricing_subtitle')}*")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 24px; text-align: center;">
            <h3 style="color: #475569; margin-top: 0;">{t('plan_free_name')}</h3>
            <div style="font-size: 28px; font-weight: 800; color: #0F172A; margin: 10px 0;">{t('plan_free_price')}</div>
            <p style="color: #64748B; font-size: 13px; min-height: 40px;">{t('plan_free_desc')}</p>
            <hr style="border-color: #F1F5F9;">
            <ul style="text-align: left; font-size: 13px; color: #334155; line-height: 1.8;">
                <td>✓ Basic raw-material risk prediction</td><br>
                <td>✓ Low / Medium / High classification</td><br>
                <td>✓ Basic trade metrics & market share</td><br>
                <td>✓ Basic Global Risk Map</td><br>
                <td>✓ Basic GDELT event count breakdown</td><br>
                <td>✓ Limited AI Chatbot queries</td>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if user_plan == "free":
            st.button(f"✓ {t('btn_current_plan')}", disabled=True, use_container_width=True, key="btn_free_active")
    with col2:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 2px solid #0F766E; border-radius: 10px; padding: 24px; text-align: center; box-shadow: 0 10px 25px rgba(15, 118, 110, 0.1);">
            <div style="background-color: #0F766E; color: white; display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 700; margin-bottom: 8px;">RECOMMENDED</div>
            <h3 style="color: #0F766E; margin-top: 0;">{t('plan_pro_name')}</h3>
            <div style="font-size: 28px; font-weight: 800; color: #0F172A; margin: 10px 0;">{t('plan_pro_price')}</div>
            <p style="color: #64748B; font-size: 13px; min-height: 40px;">{t('plan_pro_desc')}</p>
            <hr style="border-color: #F1F5F9;">
            <ul style="text-align: left; font-size: 13px; color: #334155; line-height: 1.8;">
                <td>✓ <strong>Everything in Free</strong></td><br>
                <td>✓ Detailed SHAP risk explanations</td><br>
                <td>✓ Advanced GDELT scatter insights</td><br>
                <td>✓ Alternative supplier-country matching</td><br>
                <td>✓ HHI supplier dependency analysis</td><br>
                <td>✓ Model Benchmark comparison</td><br>
                <td>✓ 1-Click Executive Report Export</td><br>
                <td>✓ Geopolitical Early Warning Radar</td><br>
                <td>✓ Extended AI Chatbot usage</td>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if user_plan == "pro":
            st.button(f"✓ {t('btn_current_plan')}", disabled=True, use_container_width=True, key="btn_pro_active")
        else:
            if st.button(f"⚡ {t('btn_upgrade_pro')}", type="primary", use_container_width=True, key="btn_upgrade_pro_pricing"):
                st.session_state["show_demo_payment"] = True
                st.rerun()
    with col3:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 24px; text-align: center;">
            <h3 style="color: #1E3A8A; margin-top: 0;">{t('plan_enterprise_name')}</h3>
            <div style="font-size: 28px; font-weight: 800; color: #0F172A; margin: 10px 0;">{t('plan_enterprise_price')}</div>
            <p style="color: #64748B; font-size: 13px; min-height: 40px;">{t('plan_enterprise_desc')}</p>
            <hr style="border-color: #F1F5F9;">
            <ul style="text-align: left; font-size: 13px; color: #334155; line-height: 1.8;">
                <td>✓ <strong>Everything in Pro</strong></td><br>
                <td>✓ Multi-user team collaboration</td><br>
                <td>✓ Organization-level risk tracking</td><br>
                <td>✓ Custom report branding</td><br>
                <td>✓ Priority AI Assistant model</td><br>
                <td>✓ Dedicated SLA & support</td>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if user_plan == "enterprise":
            st.button(f"✓ {t('btn_current_plan')}", disabled=True, use_container_width=True, key="btn_ent_active")
        else:
            st.button(f"💬 {t('btn_contact_enterprise')}", use_container_width=True, key="btn_contact_sales")
def main():
    if "language" not in st.session_state:
        st.session_state["language"] = "en"
    if "authenticated_user" not in st.session_state:
        st.session_state["authenticated_user"] = None
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "show_demo_payment" not in st.session_state:
        st.session_state["show_demo_payment"] = False
    if "show_profile" not in st.session_state:
        st.session_state["show_profile"] = False
    if "show_pricing" not in st.session_state:
        st.session_state["show_pricing"] = False
    df_integrated = load_dataset()
    metrics_summary = load_metrics()
    predictor = RiskPredictor()
    alt_analyzer = AlternativeSupplierAnalyzer()
    assistant = StraviaAssistant()
    st.sidebar.markdown(f"### {t('lang_selector_label')}")
    inv_lang = {v: k for k, v in SUPPORTED_LANGUAGES.items()}
    curr_lang_name = SUPPORTED_LANGUAGES.get(st.session_state["language"], "English")
    selected_lang_name = st.sidebar.selectbox(
        t("lang_selector_label"),
        options=list(SUPPORTED_LANGUAGES.values()),
        index=list(SUPPORTED_LANGUAGES.values()).index(curr_lang_name),
        label_visibility="collapsed"
    )
    st.session_state["language"] = inv_lang[selected_lang_name]
    st.sidebar.markdown("---")
    user = st.session_state["authenticated_user"]
    if user is None:
        st.sidebar.markdown(f"### {t('nav_login')}")
        nav_choice = st.sidebar.radio(
            "Auth Menu",
            [t("nav_login"), t("nav_register"), t("nav_pricing")],
            index=0 if st.session_state["auth_view"] == "login" else (1 if st.session_state["auth_view"] == "register" else 2),
            label_visibility="collapsed"
        )
        if nav_choice == t("nav_login"):
            st.session_state["auth_view"] = "login"
        elif nav_choice == t("nav_register"):
            st.session_state["auth_view"] = "register"
        else:
            st.session_state["auth_view"] = "pricing"
        st.markdown(f"""
        <div style="padding: 10px 0px 20px 0px; border-bottom: 2px solid #E2E8F0; margin-bottom: 25px;">
            <h1 style="color: #0F172A; font-size: 32px; font-weight: 800; margin: 0;">{t('page_title')}</h1>
            <p style="color: #475569; font-size: 16px; margin-top: 4px;">{t('page_subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state["auth_view"] == "login":
            c1, c2 = st.columns([1.15, 0.85], gap="large")
            with c1:
                st.markdown("""
                <div class="auth-illustration">
                    <p class="auth-kicker">STRAVIA AI / GLOBAL FLOW</p>
                    <p class="auth-caption">A friendly crew for every important handoff, route, and risk signal.</p>
                    <svg viewBox="0 0 620 390" role="img" aria-label="Cartoon supply chain team with warehouse, packages, truck, and cargo ship" style="width:100%; height:auto; display:block;">
                        <path d="M40 325 C160 295 260 340 365 315 S525 285 590 315" fill="none" stroke="#99DAD1" stroke-width="10" stroke-linecap="round" opacity=".65"/>
                        <path d="M60 110 H560" stroke="#B7E8E1" stroke-width="3" stroke-dasharray="8 12"/>
                        <circle cx="90" cy="110" r="9" fill="#0F766E"/><circle cx="310" cy="110" r="9" fill="#38BDF8"/><circle cx="530" cy="110" r="9" fill="#F59E0B"/>
                        <path d="M90 110 Q200 45 310 110 T530 110" fill="none" stroke="#64CFC3" stroke-width="3" stroke-dasharray="7 8"/>
                        <g transform="translate(42 150)">
                            <path d="M0 80 L0 10 L72 10 L104 34 L104 80 Z" fill="#D8F2EE" stroke="#0F766E" stroke-width="4"/>
                            <path d="M0 36 H104 M25 10 V80 M52 10 V80 M78 10 V80" stroke="#70BDB4" stroke-width="3"/>
                            <path d="M18 80 V51 H45 V80 M61 80 V51 H88 V80" fill="#FFFFFF" stroke="#0F766E" stroke-width="3"/>
                            <circle cx="52" cy="-4" r="22" fill="#FFD1B3" stroke="#8B5E4A" stroke-width="3"/><path d="M31 -5 Q52 -36 74 -5" fill="#F59E0B" stroke="#8B5E4A" stroke-width="4"/>
                            <circle cx="45" cy="-1" r="3" fill="#334155"/><circle cx="60" cy="-1" r="3" fill="#334155"/><path d="M48 9 Q53 14 59 9" fill="none" stroke="#8B5E4A" stroke-width="2"/>
                        </g>
                        <g transform="translate(205 197)">
                            <rect x="0" y="30" width="105" height="64" rx="10" fill="#F8C65D" stroke="#A16207" stroke-width="4"/><path d="M22 30 V94 M52 30 V94 M82 30 V94" stroke="#D89020" stroke-width="3"/>
                            <path d="M15 54 H90" stroke="#FFF1B8" stroke-width="5"/><path d="M0 94 H105" stroke="#A16207" stroke-width="4"/>
                            <circle cx="24" cy="112" r="13" fill="#475569"/><circle cx="82" cy="112" r="13" fill="#475569"/><circle cx="24" cy="112" r="5" fill="#CBD5E1"/><circle cx="82" cy="112" r="5" fill="#CBD5E1"/>
                            <rect x="102" y="50" width="32" height="44" rx="7" fill="#38BDF8" stroke="#0369A1" stroke-width="4"/>
                            <circle cx="118" cy="25" r="22" fill="#FFD1B3" stroke="#8B5E4A" stroke-width="3"/><path d="M98 21 Q118 -7 139 20" fill="#334155" stroke="#1E293B" stroke-width="4"/>
                            <circle cx="111" cy="24" r="3" fill="#334155"/><circle cx="125" cy="24" r="3" fill="#334155"/><path d="M113 34 Q118 39 124 34" fill="none" stroke="#8B5E4A" stroke-width="2"/>
                        </g>
                        <g transform="translate(400 190)">
                            <path d="M0 75 H154 L132 103 H25 Z" fill="#0F766E" stroke="#115E59" stroke-width="4"/><path d="M18 75 V38 H108 V75" fill="#D9F5F1" stroke="#0F766E" stroke-width="4"/><path d="M108 38 H139 V75" fill="#BAE6FD" stroke="#0369A1" stroke-width="4"/><path d="M20 53 H105" stroke="#7DD3FC" stroke-width="4"/>
                            <circle cx="38" cy="106" r="13" fill="#475569"/><circle cx="120" cy="106" r="13" fill="#475569"/><circle cx="38" cy="106" r="5" fill="#CBD5E1"/><circle cx="120" cy="106" r="5" fill="#CBD5E1"/>
                            <circle cx="70" cy="17" r="22" fill="#FFD1B3" stroke="#8B5E4A" stroke-width="3"/><path d="M49 12 Q70 -13 91 12" fill="#F97316" stroke="#9A3412" stroke-width="4"/><circle cx="63" cy="17" r="3" fill="#334155"/><circle cx="77" cy="17" r="3" fill="#334155"/><path d="M65 27 Q70 32 76 27" fill="none" stroke="#8B5E4A" stroke-width="2"/>
                        </g>
                        <path d="M470 335 H575" stroke="#0F766E" stroke-width="5" stroke-linecap="round"/><path d="M500 335 Q525 310 550 335" fill="none" stroke="#0F766E" stroke-width="5"/>
                    </svg>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
                st.markdown(f"### 🔑 {t('login_header')}")
                st.markdown(f"*{t('login_subtitle')}*")
                with st.form("login_form"):
                    email_input = st.text_input(t("field_email"), placeholder="user@example.com")
                    pass_input = st.text_input(t("field_password"), type="password")
                    submit_login = st.form_submit_button(t("btn_login"), type="primary", use_container_width=True)
                    if submit_login:
                        res = auth_mgr.authenticate_user(email_input, pass_input)
                        if res["status"] == "success":
                            st.session_state["authenticated_user"] = {
                                "user_id": res["user_id"],
                                "full_name": res["full_name"],
                                "email": res["email"],
                                "plan": res["plan"]
                            }
                            st.success(t("msg_login_success"))
                            st.rerun()
                        else:
                            st.error(res["message"])
                if st.button("New user? Create a free account", use_container_width=True):
                    st.session_state["auth_view"] = "register"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        elif st.session_state["auth_view"] == "register":
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f"### 📝 {t('register_header')}")
                st.markdown(f"*{t('register_subtitle')}*")
                with st.form("reg_form"):
                    full_name_in = st.text_input(t("field_fullname"), placeholder="Jane Doe")
                    email_in = st.text_input(t("field_email"), placeholder="jane@example.com")
                    pass1_in = st.text_input(t("field_password"), type="password")
                    pass2_in = st.text_input(t("field_confirm_password"), type="password")
                    submit_reg = st.form_submit_button(t("btn_register"), type="primary", use_container_width=True)
                    if submit_reg:
                        res = auth_mgr.register_user(full_name_in, email_in, pass1_in, pass2_in)
                        if res["status"] == "success":
                            st.success(t("msg_reg_success"))
                            st.session_state["auth_view"] = "login"
                            st.rerun()
                        else:
                            st.error(res["message"])
                if st.button("Already have an account? Sign In", use_container_width=True):
                    st.session_state["auth_view"] = "login"
                    st.rerun()
        elif st.session_state["auth_view"] == "pricing":
            render_pricing_page(user_plan="free")
        return
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #F7FCFA;
            background-image:
                linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(231, 248, 246, 0.34) 100%),
                url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 1000'><defs><linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='%23FFFDF5'/><stop offset='0.58' stop-color='%23E8F7FF'/><stop offset='1' stop-color='%23DDF5EF'/></linearGradient><linearGradient id='hill' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='%23B8E4D8'/><stop offset='1' stop-color='%2373C8B6'/></linearGradient><linearGradient id='hill2' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='%23D7F1E6'/><stop offset='1' stop-color='%23A8DCCE'/></linearGradient></defs><rect width='1600' height='1000' fill='url(%23sky)'/><circle cx='1310' cy='155' r='82' fill='%23FFE6A8' opacity='.82'/><circle cx='1310' cy='155' r='112' fill='none' stroke='%23F6C969' stroke-width='3' opacity='.25'/><g fill='%23FFFFFF' opacity='.78'><path d='M180 205c18-42 83-48 113-8 20-15 61-7 68 28H116c8-18 32-28 64-20z'/><path d='M1120 290c15-35 66-39 91-6 18-12 47-4 53 23h-199c7-15 27-23 55-17z'/></g><path d='M0 610 Q230 480 450 620 T870 570 T1280 600 T1600 540 V1000 H0Z' fill='url(%23hill2)'/><path d='M0 715 Q260 540 520 700 T980 655 T1390 700 T1600 640 V1000 H0Z' fill='url(%23hill)' opacity='.88'/><path d='M0 810 Q330 700 650 810 T1240 770 T1600 790 V1000 H0Z' fill='%2358B59D' opacity='.48'/><g fill='none' stroke='%230F766E' stroke-width='3' opacity='.24'><path d='M190 720 Q480 450 785 635 T1370 510'/><path d='M110 820 Q435 600 800 760 T1510 650'/></g><g fill='%23F29F9F' opacity='.8'><circle cx='250' cy='635' r='7'/><circle cx='277' cy='612' r='5'/><circle cx='307' cy='641' r='6'/><circle cx='1355' cy='631' r='6'/><circle cx='1382' cy='606' r='5'/><circle cx='1411' cy='641' r='7'/></g><g fill='%23FFFFFF' opacity='.42'><circle cx='405' cy='350' r='4'/><circle cx='438' cy='392' r='3'/><circle cx='970' cy='168' r='4'/><circle cx='1010' cy='210' r='3'/><circle cx='720' cy='285' r='3'/></g><g transform='translate(90 735)' opacity='.6'><path d='M0 120 Q42 24 84 120' fill='none' stroke='%235A9E83' stroke-width='7'/><path d='M42 120 V0' stroke='%235A9E83' stroke-width='6'/><path d='M42 18 Q7 8 2 38 Q28 46 42 42 M42 54 Q76 39 84 70 Q60 77 42 72 M42 82 Q12 72 8 100 Q29 106 42 100' fill='%236AC09F'/></g><g transform='translate(1450 735)' opacity='.6'><path d='M0 120 Q42 24 84 120' fill='none' stroke='%235A9E83' stroke-width='7'/><path d='M42 120 V0' stroke='%235A9E83' stroke-width='6'/><path d='M42 18 Q7 8 2 38 Q28 46 42 42 M42 54 Q76 39 84 70 Q60 77 42 72 M42 82 Q12 72 8 100 Q29 106 42 100' fill='%236AC09F'/></g></svg>");
            background-repeat: no-repeat;
            background-size: cover;
            background-position: center top;
            background-attachment: fixed;
        }
        [data-testid="stMainBlockContainer"]::before {
            border-color: rgba(78, 143, 126, 0.18);
            background-color: rgba(255, 255, 255, 0.76);
            background-image: linear-gradient(rgba(15, 118, 110, 0.028) 1px, transparent 1px), linear-gradient(90deg, rgba(15, 118, 110, 0.028) 1px, transparent 1px);
            box-shadow: 0 22px 70px rgba(49, 126, 105, 0.12);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(246, 253, 249, 0.97) 0%, rgba(239, 249, 255, 0.97) 100%);
            border-right-color: rgba(78, 143, 126, 0.18);
        }
        [data-testid="stSidebar"] > div:first-child {
            background-image: radial-gradient(circle at 18% 12%, rgba(242, 159, 159, 0.16) 0 2px, transparent 2.5px), radial-gradient(circle at 82% 34%, rgba(56, 189, 248, 0.12) 0 2px, transparent 2.5px);
        }
        .stAppHeader {
            background-color: rgba(255, 255, 255, 0.84);
        }
    </style>
    """, unsafe_allow_html=True)
    user_plan = sub_mgr.get_user_plan(user["user_id"])
    st.session_state["authenticated_user"]["plan"] = user_plan
    badge_class_plan = f"plan-badge-{user_plan}"
    st.sidebar.markdown(f"""
    <div class="user-profile-box">
        <div style="font-weight: 700; color: #0F172A; font-size: 15px;">👤 {user['full_name']}</div>
        <div style="font-size: 12px; color: #64748B; margin-bottom: 6px;">{user['email']}</div>
        <div><span class="{badge_class_plan}">{user_plan.upper()} PLAN</span></div>
    </div>
    """, unsafe_allow_html=True)
    c_sb1, c_sb2 = st.columns(2)
    if st.sidebar.button(f"👤 {t('nav_account')}", use_container_width=True):
        st.session_state["show_profile"] = not st.session_state.get("show_profile", False)
        st.session_state["show_pricing"] = False
        st.rerun()
    if st.sidebar.button(f"💳 {t('nav_pricing')}", use_container_width=True):
        st.session_state["show_pricing"] = not st.session_state.get("show_pricing", False)
        st.session_state["show_profile"] = False
        st.rerun()
    if st.sidebar.button(f"🚪 {t('nav_logout')}", type="secondary", use_container_width=True):
        st.session_state["authenticated_user"] = None
        st.session_state["auth_view"] = "login"
        st.session_state["show_profile"] = False
        st.session_state["show_pricing"] = False
        st.session_state["show_demo_payment"] = False
        st.rerun()
    if st.session_state.get("show_demo_payment"):
        st.markdown("---")
        st.markdown(f"## 🛡️ {t('demo_payment_header')}")
        st.warning(f"⚠️ {t('demo_payment_notice')}")
        col_left, col_right = st.columns([1, 1.4])
        with col_left:
            st.markdown(f"### 📋 {t('order_summary_title')}")
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; padding: 20px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;">MERCHANT</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 12px;">STRAVIA AI Technologies Pvt. Ltd.</div>
                <hr style="border-color: #F1F5F9; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #334155; font-weight: 600;">{t('order_item_plan')}</span>
                    <span style="color: #0F172A; font-weight: 700;">₹422.88</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; color: #64748B;">
                    <span>GST (18% Included)</span>
                    <span>₹76.12</span>
                </div>
                <hr style="border-color: #CBD5E1; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">Total Amount</span>
                    <span style="font-size: 24px; font-weight: 800; color: #0F766E;">₹499.00</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_right:
            st.markdown("### 💳 Payment Method")
            tab_upi, tab_net, tab_card, tab_wallet = st.tabs([
                t("pay_tab_upi"),
                t("pay_tab_netbanking"),
                t("pay_tab_card"),
                t("pay_tab_wallet")
            ])
            trigger_payment = False
            method_selected = ""
            with tab_upi:
                st.markdown(f"#### {t('pay_tab_upi')}")
                c_qr1, c_qr2 = st.columns([1, 1.2])
                with c_qr1:
                    st.markdown("""
                    <div style="background-color: #FFFFFF; border: 2px solid #0F766E; padding: 12px; border-radius: 10px; text-align: center;">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa=stravia.demo@okaxis&pn=STRAVIA%20AI&am=499.00&cu=INR" 
                             alt="Demo QR Code" style="width: 140px; height: 140px;" />
                        <div style="font-size: 11px; font-weight: 700; color: #0F766E; margin-top: 6px;">BHIM UPI / GPay / PhonePe / Paytm</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_qr2:
                    upi_input = st.text_input(t("upi_enter_id"), value="stravia.demo@okaxis", placeholder=t("upi_placeholder"))
                    st.caption(t("upi_qr_instruction"))
                    if st.button(t("btn_pay_now"), type="primary", use_container_width=True, key="btn_pay_upi"):
                        trigger_payment = True
                        method_selected = f"UPI ({upi_input})"
            with tab_net:
                st.markdown(f"#### {t('pay_tab_netbanking')}")
                bank_options = ["State Bank of India (SBI)", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "Punjab National Bank (PNB)"]
                selected_bank = st.selectbox(t("select_bank"), bank_options, index=0)
                st.info(f"💡 You will be securely redirected to {selected_bank} Netbanking portal (Demo Simulation).")
                if st.button(t("btn_pay_now"), type="primary", use_container_width=True, key="btn_pay_net"):
                    trigger_payment = True
                    method_selected = f"Netbanking ({selected_bank})"
            with tab_card:
                st.markdown(f"#### {t('pay_tab_card')}")
                card_num = st.text_input(t("card_number"), value="4532 •••• •••• 8901")
                col_cd1, col_cd2 = st.columns(2)
                card_exp = col_cd1.text_input(t("card_expiry"), value="12/28")
                card_cvv = col_cd2.text_input(t("card_cvv"), type="password", value="123")
                card_name = st.text_input(t("card_name"), value=user["full_name"])
                if st.button(t("btn_pay_now"), type="primary", use_container_width=True, key="btn_pay_card"):
                    trigger_payment = True
                    method_selected = f"Card ({card_num[-4:] if len(card_num)>=4 else '8901'})"
            with tab_wallet:
                st.markdown(f"#### {t('pay_tab_wallet')}")
                wallet_options = ["Paytm Wallet", "PhonePe Wallet", "Amazon Pay Balance", "MobiKwik"]
                selected_wallet = st.selectbox(t("select_wallet"), wallet_options, index=0)
                st.info(f"💡 Link your {selected_wallet} account to complete 1-click checkout.")
                if st.button(t("btn_pay_now"), type="primary", use_container_width=True, key="btn_pay_wallet"):
                    trigger_payment = True
                    method_selected = f"Wallet ({selected_wallet})"
            if st.button("Cancel & Return to Workspace", use_container_width=True, key="btn_cancel_payment"):
                st.session_state["show_demo_payment"] = False
                st.rerun()
            if trigger_payment:
                with st.spinner(t("payment_processing")):
                    time.sleep(1.0)
                    txn_id = f"TXN_STRAVIA_{random.randint(100000, 999999)}"
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
                    res = sub_mgr.upgrade_subscription(user["user_id"], "pro")
                    if res["status"] == "success":
                        st.session_state["authenticated_user"]["plan"] = "pro"
                        st.session_state["last_receipt"] = {
                            "txn_id": txn_id,
                            "timestamp": now_str,
                            "amount": "₹499.00",
                            "method": method_selected,
                            "plan": "STRAVIA Pro Monthly Plan"
                        }
                        st.session_state["show_demo_payment"] = False
                        st.success(t("demo_payment_success"))
                        st.rerun()
                    else:
                        st.error(res["message"])
        st.markdown("---")
    if st.session_state.get("last_receipt"):
        rcpt = st.session_state["last_receipt"]
        st.markdown(f"""
        <div style="background-color: #ECFDF5; border: 2px solid #059669; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
            <h3 style="color: #065F46; margin-top: 0;">🧾 {t('receipt_header')}</h3>
            <div style="font-size: 14px; color: #064E3B; line-height: 1.8;">
                <strong>{t('receipt_txn_id')}:</strong> <span style="font-family: monospace;">{rcpt['txn_id']}</span><br>
                <strong>{t('receipt_status')}:</strong> <span style="background-color: #D1FAE5; color: #065F46; padding: 2px 8px; border-radius: 10px; font-weight: 700;">SUCCESS</span><br>
                <strong>Plan:</strong> {rcpt['plan']}<br>
                <strong>Amount:</strong> {rcpt['amount']}<br>
                <strong>Payment Method:</strong> {rcpt['method']}<br>
                <strong>{t('receipt_date')}:</strong> {rcpt['timestamp']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✓ Dismiss Receipt & Return to Workspace", type="primary"):
            st.session_state["last_receipt"] = None
            st.rerun()
    if st.session_state.get("show_profile"):
        st.markdown(f"## 👤 {t('account_profile_header')}")
        c_prof1, c_prof2 = st.columns(2)
        with c_prof1:
            st.markdown(f"**{t('account_name')}:** {user['full_name']}")
            st.markdown(f"**{t('account_email')}:** {user['email']}")
            st.markdown(f"**{t('account_status')}:** <span style='color: #059669; font-weight: 700;'>Active</span>", unsafe_allow_html=True)
            st.markdown(f"**{t('account_plan')}:** <span class='{badge_class_plan}'>{user_plan.upper()}</span>", unsafe_allow_html=True)
            if user_plan == "free":
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"⚡ {t('btn_upgrade_pro')}", type="primary"):
                    st.session_state["show_demo_payment"] = True
                    st.session_state["show_profile"] = False
                    st.rerun()
        st.markdown("---")
    if st.session_state.get("show_pricing"):
        render_pricing_page(user_plan=user_plan)
        st.markdown("---")
    st.sidebar.markdown("---")
    st.sidebar.header(t("selection_panel_header"))
    available_products = sorted(df_integrated["product_name"].unique())
    selected_product = st.sidebar.selectbox(t("select_raw_material"), available_products, index=0)
    suppliers_for_product = sorted(df_integrated[df_integrated["product_name"] == selected_product]["exporter_name"].unique())
    selected_supplier = st.sidebar.selectbox(t("select_supplier_country"), suppliers_for_product, index=0)
    selected_year = st.sidebar.selectbox(t("select_target_year"), [2024, 2023, 2022], index=0)
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('project_metadata_header')}")
    st.sidebar.markdown(f"**{t('data_sources_label')}** CEPII BACI + GDELT")
    st.sidebar.markdown(f"**{t('target_year_label')}** 2022–2024")
    best_model_name = metrics_summary.get("best_model", "XGBoost")
    st.sidebar.markdown(f"**{t('ml_best_model_label')}** <span style='color: #059669; font-weight: 700;'>{best_model_name}</span>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding: 10px 0px 20px 0px; border-bottom: 2px solid #E2E8F0; margin-bottom: 25px;">
        <h1 style="color: #0F172A; font-size: 32px; font-weight: 800; margin: 0;">{t('page_title')}</h1>
        <p style="color: #475569; font-size: 16px; margin-top: 4px;">{t('page_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
    pred_res = predictor.predict_relationship(df_integrated, selected_product, selected_supplier, selected_year)
    if pred_res["status"] == "error":
        st.error(pred_res["message"])
        return
    risk_label = pred_res["predicted_risk_level"]
    risk_score = pred_res["risk_score"]
    col1, col2, col3, col4, col5 = st.columns(5)
    badge_class = "risk-badge-low" if "LOW" in risk_label else ("risk-badge-high" if "HIGH" in risk_label else "risk-badge-medium")
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{t('predicted_risk_level')}</div>
            <div style="margin-top: 8px;"><span class="{badge_class}">{risk_label}</span></div>
            <div style="font-size: 11px; color: #64748B; margin-top: 6px;">{t('score_sublabel')} {risk_score:.1f}/100</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        val_m = pred_res["trade_value_usd_k"] / 1000.0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{t('trade_value_kpi')}</div>
            <div class="metric-value">${val_m:.2f}M</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">{t('yoy_sublabel')} {pred_res['yoy_trade_change']:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        hhi_val = pred_res["supplier_hhi"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{t('supplier_hhi_kpi')}</div>
            <div class="metric-value">{hhi_val:.0f}</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">{t('market_share_sublabel')} {pred_res['supplier_share']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        events = pred_res["recent_event_count"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{t('gdelt_events_kpi')}</div>
            <div class="metric-value">{events}</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">{t('conflicts_sublabel')} {pred_res['conflict_event_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{t('ml_model_used_kpi')}</div>
            <div class="metric-value" style="font-size: 18px; margin-top: 6px;">{pred_res['model_used']}</div>
            <div style="font-size: 11px; color: #059669; margin-top: 4px;">{t('f1_optimized_sublabel')}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        t("tab_overview"),
        t("tab_trade_analysis"),
        t("tab_event_risk"),
        t("tab_risk_prediction"),
        t("tab_alternative_suppliers"),
        t("tab_model_benchmark"),
        t("tab_assistant"),
        t("tab_global_map")
    ])
    alts_df = alt_analyzer.get_alternative_suppliers(df_integrated, selected_product, selected_supplier, selected_year)
    with tab1:
        st.subheader(t("overview_header", product=selected_product, supplier=selected_supplier, year=selected_year))
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"#### {t('key_trade_metrics_header')}")
            summary_df = pd.DataFrame({
                t("indicator_product"): [selected_product],
                t("indicator_supplier"): [selected_supplier],
                t("indicator_value"): [f"${pred_res['trade_value_usd_k']:,.2f}"],
                t("indicator_quantity"): [f"{pred_res['quantity_tons']:,.2f} Tons"],
                t("indicator_share"): [f"{pred_res['supplier_share']:.2f}%"],
                t("indicator_hhi"): [f"{pred_res['supplier_hhi']:.1f}"],
                t("indicator_yoy"): [f"{pred_res['yoy_trade_change']:+.2f}%"]
            }).T.reset_index()
            summary_df.columns = ["Metric", "Value"]
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        with c2:
            st.markdown(f"#### {t('overall_risk_gauge_header')}")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': t("composite_risk_score_title"), 'font': {'size': 16}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "#1E293B"},
                    'steps': [
                        {'range': [0, 35], 'color': "#D1FAE5"},
                        {'range': [35, 60], 'color': "#FEF3C7"},
                        {'range': [60, 100], 'color': "#FEE2E2"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': risk_score
                    }
                }
            ))
            fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="#FFFFFF")
            st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown(f"#### {t('executive_summary_header')}")
        best_alt_text = f"**{alts_df.iloc[0]['Country']}**" if not alts_df.empty else "None identified"
        summary_body = t(
            "summary_text_template",
            product=selected_product,
            supplier=selected_supplier,
            risk_label=risk_label,
            score=risk_score,
            hhi=pred_res['supplier_hhi'],
            events=pred_res['recent_event_count'],
            best_alt=best_alt_text
        )
        st.markdown(f"""
        <div class="summary-box">
            <strong>{t('decision_statement_label')}</strong><br>
            {summary_body}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if sub_mgr.can_access(user_plan, "executive_report_export"):
            with st.expander(f"📄 {t('btn_export_report')}"):
                md_report = ExecutiveReportGenerator.generate_markdown_report(
                    pred_res, alts_df, selected_product, selected_supplier, selected_year, lang_code=st.session_state["language"]
                )
                st.markdown(md_report)
                st.download_button(
                    label=f"⬇️ Download {selected_product}_{selected_supplier}_{selected_year}_Report.md",
                    data=md_report,
                    file_name=f"STRAVIA_Executive_Report_{selected_product}_{selected_supplier}_{selected_year}.md",
                    mime="text/markdown"
                )
        else:
            render_locked_feature_card("Executive Brief Export", "Downloadable C-level Markdown & PDF executive briefings require a STRAVIA Pro subscription.")
    with tab2:
        st.subheader(t("baci_trade_header"))
        rel_df = df_integrated[(df_integrated["product_name"] == selected_product) & (df_integrated["exporter_name"] == selected_supplier)].sort_values("year")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### {t('trade_trend_header')}")
            fig_trend = px.line(
                rel_df, x="year", y="trade_value", markers=True,
                title=f"{t('axis_trade_value')} - {selected_supplier}",
                labels={"trade_value": t("axis_trade_value"), "year": t("axis_year")},
                color_discrete_sequence=["#2563EB"]
            )
            fig_trend.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC")
            st.plotly_chart(fig_trend, use_container_width=True)
        with c2:
            st.markdown(f"#### {t('market_share_header')}")
            all_suppliers_prod = df_integrated[(df_integrated["product_name"] == selected_product) & (df_integrated["year"] == selected_year)]
            fig_pie = px.pie(
                all_suppliers_prod, names="exporter_name", values="trade_value",
                title=t("pie_chart_title", product=selected_product, year=selected_year),
                hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(paper_bgcolor="#FFFFFF")
            st.plotly_chart(fig_pie, use_container_width=True)
    with tab3:
        st.subheader(t("gdelt_header"))
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### {t('event_breakdown_header', supplier=selected_supplier, year=selected_year)}")
            categories = [t("cat_conflict"), t("cat_instability"), t("cat_disaster"), t("cat_sanctions")]
            counts = [
                pred_res["conflict_event_count"],
                int(df_integrated[(df_integrated["exporter_name"]==selected_supplier) & (df_integrated["year"]==selected_year)]["instability_event_count"].values[0]) if not df_integrated[(df_integrated["exporter_name"]==selected_supplier) & (df_integrated["year"]==selected_year)].empty else 0,
                int(df_integrated[(df_integrated["exporter_name"]==selected_supplier) & (df_integrated["year"]==selected_year)]["disaster_event_count"].values[0]) if not df_integrated[(df_integrated["exporter_name"]==selected_supplier) & (df_integrated["year"]==selected_year)].empty else 0,
                pred_res["sanction_event_count"]
            ]
            fig_bar = px.bar(
                x=categories, y=counts,
                labels={"x": t("event_category_axis"), "y": t("recorded_event_count_axis")},
                title=f"GDELT Events: {selected_supplier}",
                color=categories, color_discrete_sequence=["#EF4444", "#F59E0B", "#10B981", "#8B5CF6"]
            )
            fig_bar.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.markdown(f"#### {t('intensity_vs_tone_header')}")
            if sub_mgr.can_access(user_plan, "advanced_gdelt_scatter"):
                supplier_events = df_integrated[df_integrated["exporter_name"] == selected_supplier].sort_values("year")
                fig_scatter = px.scatter(
                    supplier_events, x="negative_event_intensity", y="avg_tone", size="event_count", color="year",
                    hover_name="year", title=t("scatter_chart_title", supplier=selected_supplier),
                    labels={"negative_event_intensity": t("negative_intensity_axis"), "avg_tone": t("avg_tone_axis")}
                )
                fig_scatter.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC")
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                render_locked_feature_card("Advanced GDELT Intensity vs Tone Scatter Analytics", "Detailed news tone sentiment correlation charts are available with STRAVIA Pro.")
    with tab4:
        st.subheader(t("ml_risk_header"))
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### {t('risk_prob_header')}")
            prob_df = pd.DataFrame({
                t("risk_class_axis"): [t("prob_low_risk"), t("prob_medium_risk"), t("prob_high_risk")],
                t("probability_axis"): [pred_res["probabilities"]["Low"], pred_res["probabilities"]["Medium"], pred_res["probabilities"]["High"]]
            })
            fig_prob = px.bar(
                prob_df, x=t("risk_class_axis"), y=t("probability_axis"), color=t("risk_class_axis"),
                color_discrete_map={t("prob_low_risk"): "#10B981", t("prob_medium_risk"): "#F59E0B", t("prob_high_risk"): "#EF4444"},
                title=t("prob_chart_title", model=pred_res['model_used']), text_auto=".2%"
            )
            fig_prob.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", showlegend=False)
            st.plotly_chart(fig_prob, use_container_width=True)
        with c2:
            st.markdown(f"#### {t('top_risk_factors_header')}")
            if sub_mgr.can_access(user_plan, "detailed_risk_explanation"):
                for idx, factor in enumerate(pred_res["top_risk_factors"], 1):
                    st.markdown(f"**{idx}.** {factor}")
            else:
                render_locked_feature_card("Detailed SHAP Risk Factor Attribution", "Granular machine learning risk feature importances require STRAVIA Pro.")
    with tab5:
        st.subheader(t("alt_supplier_header", product=selected_product))
        st.markdown(t("alt_supplier_subtext"))
        if sub_mgr.can_access(user_plan, "alternative_suppliers"):
            if not alts_df.empty:
                localized_alts = alts_df.copy()
                localized_alts.columns = [
                    t("col_rank"), t("col_country"), t("col_iso"), t("col_capability"),
                    t("col_volume"), t("col_risk_level"), t("col_risk_score"), t("col_match_score")
                ]
                st.dataframe(localized_alts, use_container_width=True, hide_index=True)
                fig_alt = px.bar(
                    alts_df, x="Country", y="Match Score", color="Risk Level",
                    color_discrete_map={"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#EF4444"},
                    title=t("alt_ranking_chart_title")
                )
                fig_alt.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC")
                st.plotly_chart(fig_alt, use_container_width=True)
            else:
                st.info(t("no_alt_found"))
        else:
            render_locked_feature_card("Alternative Supplier Matching Intelligence", "Automated country matching and supplier diversification optimization requires STRAVIA Pro.")
    with tab6:
        st.subheader(t("benchmark_header"))
        st.markdown(t("benchmark_subtext"))
        if sub_mgr.can_access(user_plan, "model_benchmark"):
            metrics_dict = metrics_summary.get("metrics", {})
            if metrics_dict:
                bench_data = []
                for m_name, m_vals in metrics_dict.items():
                    bench_data.append({
                        t("col_algorithm"): m_name,
                        t("col_accuracy"): f"{m_vals['accuracy']:.4f}",
                        t("col_precision"): f"{m_vals['precision_macro']:.4f}",
                        t("col_recall"): f"{m_vals['recall_macro']:.4f}",
                        t("col_f1_macro"): f"{m_vals['f1_macro']:.4f}",
                        t("col_f1_weighted"): f"{m_vals['f1_weighted']:.4f}"
                    })
                df_bench = pd.DataFrame(bench_data)
                st.dataframe(df_bench, use_container_width=True, hide_index=True)
                df_bench["F1_num"] = df_bench[t("col_f1_macro")].astype(float)
                fig_bench = px.bar(
                    df_bench, x=t("col_algorithm"), y="F1_num", color=t("col_algorithm"),
                    title=t("chart_f1_title"), text_auto=".4f",
                    color_discrete_sequence=["#3B82F6", "#10B981", "#8B5CF6"]
                )
                fig_bench.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", showlegend=False)
                st.plotly_chart(fig_bench, use_container_width=True)
        else:
            render_locked_feature_card("ML Model Benchmark & Evaluation Report", "Comparative algorithm performance metrics (F1-Macro, Precision, Recall) require STRAVIA Pro.")
    with tab7:
        st.subheader(t("assistant_header"))
        st.markdown(t("assistant_subtext"))
        context_payload = assistant.build_context_summary(
            pred_res, alts_df, selected_product, selected_supplier, selected_year
        )
        st.markdown(f"""
        <div class="assistant-card">
            <h4 style="margin: 0 0 10px 0; color: #0F766E;">{t('assistant_current_context')}</h4>
            <div style="font-size: 14px; line-height: 1.6; color: #334155;">
                <strong>{t('indicator_product')}:</strong> {selected_product} &nbsp;|&nbsp; 
                <strong>{t('indicator_supplier')}:</strong> {selected_supplier} &nbsp;|&nbsp; 
                <strong>{t('target_year_label')}</strong> {selected_year}<br>
                <strong>{t('predicted_risk_level')}:</strong> <span class="{badge_class}">{risk_label}</span> &nbsp;|&nbsp; 
                <strong>{t('score_sublabel')}</strong> {risk_score:.1f}/100 &nbsp;|&nbsp; 
                <strong>{t('supplier_hhi_kpi')}:</strong> {pred_res['supplier_hhi']:.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if not assistant.has_active_api_key():
            st.warning(t("msg_no_api_key"))
        chat_count = len([m for m in st.session_state["chat_history"] if m["role"] == "user"])
        if user_plan == "free" and chat_count >= 3:
            st.info("💡 FREE plan allows up to 3 AI Decision Assistant queries per session. Upgrade to Pro for unlimited grounded Q&A.")
            if st.button(f"⚡ {t('btn_upgrade_pro')}", type="primary"):
                st.session_state["show_demo_payment"] = True
                st.rerun()
        st.markdown(f"##### {t('suggested_questions_label')}")
        sq_cols = st.columns(4)
        selected_sq = None
        if sq_cols[0].button(t("q1"), use_container_width=True):
            selected_sq = t("q1")
        if sq_cols[1].button(t("q2"), use_container_width=True):
            selected_sq = t("q2")
        if sq_cols[2].button(t("q3"), use_container_width=True):
            selected_sq = t("q3")
        if sq_cols[3].button(t("q4"), use_container_width=True):
            selected_sq = t("q4")
        st.markdown("<br>", unsafe_allow_html=True)
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        user_input = st.chat_input(t("assistant_placeholder"))
        prompt_to_send = selected_sq or user_input
        if prompt_to_send:
            if user_plan == "free" and chat_count >= 3:
                st.error("Free plan query limit reached. Please upgrade to Pro for unlimited AI queries.")
            else:
                st.session_state["chat_history"].append({"role": "user", "content": prompt_to_send})
                with st.chat_message("user"):
                    st.markdown(prompt_to_send)
                with st.chat_message("assistant"):
                    with st.spinner(t("msg_thinking")):
                        ans = assistant.generate_response(
                            prompt_to_send,
                            context_payload,
                            lang_code=st.session_state["language"]
                        )
                        st.markdown(ans)
                st.session_state["chat_history"].append({"role": "assistant", "content": ans})
    with tab8:
        st.subheader(t("global_map_header", product=selected_product))
        st.markdown(t("global_map_subtext"))
        df_map_prod = df_integrated[(df_integrated["product_name"] == selected_product) & (df_integrated["year"] == selected_year)].copy()
        if not df_map_prod.empty:
            fig_map = px.choropleth(
                df_map_prod,
                locations="exporter_iso3",
                color="risk_score",
                hover_name="exporter_name",
                hover_data={"risk_level": True, "trade_value": ":,.2f", "supplier_hhi": ":.0f", "negative_event_intensity": ":.1f"},
                color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
                range_color=[0, 100],
                title=f"Global Supply Risk Map: {selected_product} ({selected_year})",
                labels={"risk_score": "Risk Score", "exporter_iso3": "ISO Code"}
            )
            fig_map.update_layout(height=450, paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC", geo=dict(showframe=False, showcoastlines=True))
            st.plotly_chart(fig_map, use_container_width=True)
        st.markdown("---")
        st.subheader(t("early_warning_radar_header"))
        st.markdown(t("early_warning_subtext"))
        if sub_mgr.can_access(user_plan, "early_warning_radar"):
            warning_candidates = df_integrated[
                (df_integrated["product_name"] == selected_product) &
                (df_integrated["year"] == selected_year) &
                (df_integrated["yoy_trade_change"] >= -5.0) &
                ((df_integrated["conflict_event_count"] > 2) | (df_integrated["negative_event_intensity"] > 25.0))
            ]
            if not warning_candidates.empty:
                for _, w_row in warning_candidates.iterrows():
                    st.markdown(f"""
                    <div class="radar-card">
                        <strong style="color: #B45309; font-size: 16px;">🚨 EARLY WARNING SIGNAL — {w_row['exporter_name']} ({w_row['exporter_iso3']})</strong><br>
                        Historical trade volume remains stable (YoY: {w_row['yoy_trade_change']:+.1f}%), but GDELT geopolitical news events indicate escalating tension: 
                        <strong>{int(w_row['conflict_event_count'])} conflict events</strong> recorded with negative intensity score of <strong>{w_row['negative_event_intensity']:.1f}/100</strong>.
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No active geopolitical early warning alerts detected for stable trade routes under the current selection.")
        else:
            render_locked_feature_card("Geopolitical Early Warning Radar", "Real-time threat detection and anomaly signals require STRAVIA Pro.")
if __name__ == "__main__":
    main()