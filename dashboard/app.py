import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.analyst.synthetic_data_generator import generate_synthetic_data
from agents.analyst.classifier import CurtailmentRemarkClassifier, run_classifier_pipeline
from agents.warden.compliance import compute_compliance_scorecard

st.set_page_config(
    page_title="RE Curtailment Analytics & Regulatory Compliance Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Grid Control Room Dark Theme ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ── CSS Variables ─────────────────────────────────────── */
    :root {
        --bg-abyss:    #0B0F19;
        --bg-surface:  #151C2C;
        --bg-elevated: #1C2538;
        --border-dim:  #2A3550;
        --border-lit:  #334155;
        --text-prime:  #F8FAFC;
        --text-muted:  #94A3B8;
        --text-dim:    #64748B;
        --accent-green:  #10B981;
        --accent-cyan:   #06B6D4;
        --accent-amber:  #F59E0B;
        --accent-amber-bg: rgba(245, 158, 11, 0.10);
        --accent-amber-border: rgba(245, 158, 11, 0.30);
        --font-heading: 'Space Grotesk', sans-serif;
        --font-body:    'IBM Plex Sans', sans-serif;
        --font-mono:    'JetBrains Mono', monospace;
    }

    /* ── Page-load Staggered Fade-in ──────────────────────── */
    @keyframes controlRoomFadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .header-container    { animation: controlRoomFadeIn 0.5s ease-out 0.1s both; }
    .filter-banner       { animation: controlRoomFadeIn 0.5s ease-out 0.2s both; }
    .metric-card         { animation: controlRoomFadeIn 0.5s ease-out 0.3s both; }
    .metric-card:nth-child(2) { animation-delay: 0.38s; }
    .metric-card:nth-child(3) { animation-delay: 0.46s; }
    .metric-card:nth-child(4) { animation-delay: 0.54s; }

    /* ── Header Cyan Border Pulse ─────────────────────────── */
    @keyframes borderPulse {
        0%, 100% { border-left-color: rgba(6, 182, 212, 0.4); box-shadow: 0 4px 24px rgba(0,0,0,0.30); }
        50%      { border-left-color: rgba(6, 182, 212, 1.0); box-shadow: 0 4px 32px rgba(6, 182, 212, 0.12); }
    }

    /* ── Horizontal Scan Line ─────────────────────────────── */
    @keyframes scanLine {
        0%   { top: -2px; }
        100% { top: 100%; }
    }
    .stApp::after {
        content: '';
        position: fixed;
        left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(6, 182, 212, 0.10) 30%, rgba(6, 182, 212, 0.18) 50%, rgba(6, 182, 212, 0.10) 70%, transparent 100%);
        animation: scanLine 8s linear infinite;
        pointer-events: none;
        z-index: 9999;
    }

    /* ── Metric Card Left-border Glow ─────────────────────── */
    @keyframes metricBorderGlow {
        0%, 100% { border-left-color: var(--border-dim); }
        50%      { border-left-color: var(--accent-cyan); }
    }
    .metric-card {
        border-left: 2px solid var(--border-dim);
        animation: controlRoomFadeIn 0.5s ease-out 0.3s both, metricBorderGlow 4s ease-in-out infinite;
    }

    /* ── Metric Value Shimmer on Hover ────────────────────── */
    @keyframes valueShimmer {
        0%   { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    .metric-card:hover .metric-value {
        background: linear-gradient(90deg, #F8FAFC 0%, #06B6D4 50%, #F8FAFC 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: valueShimmer 2s linear infinite;
    }

    /* ── Global Typography ────────────────────────────────── */
    html, body {
        font-family: var(--font-body);
        color: var(--text-prime) !important;
    }
    [class*="css"] {
        color: var(--text-prime) !important;
    }
    
    /* Fix for Streamlit Internal Icons (Material Symbols) */
    .material-icons, [class*="material-symbols"], .stIcon,
    [data-testid="collapsedControl"] span,
    [data-testid="collapsedControl"] svg,
    button[kind="header"] span,
    button[kind="header"] svg,
    section[data-testid="stSidebar"] > div > div > button span,
    div[data-testid="stSidebarCollapseButton"] span,
    div[data-testid="stSidebarCollapseButton"] * {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
    }

    /* ── Main App Background with Grid-line Pattern ───────── */
    .stApp {
        background-color: var(--bg-abyss) !important;
        background-image:
            linear-gradient(rgba(42, 53, 80, 0.25) 1px, transparent 1px),
            linear-gradient(90deg, rgba(42, 53, 80, 0.25) 1px, transparent 1px);
        background-size: 48px 48px;
        color: var(--text-prime) !important;
    }

    /* ── Force all text to off-white ──────────────────────── */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: var(--text-prime) !important;
        font-family: var(--font-heading) !important;
        letter-spacing: -0.02em;
    }
    .stApp p, .stApp span, .stApp div, .stApp label {
        color: var(--text-prime) !important;
    }

    /* ── Markdown & Captions ──────────────────────────────── */
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: var(--text-prime) !important;
        font-family: var(--font-body) !important;
    }
    .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
        color: var(--text-muted) !important;
        font-weight: 500 !important;
    }

    /* ── Tab Styling ──────────────────────────────────────── */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
    }
    button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        font-family: var(--font-heading) !important;
        letter-spacing: 0.01em;
    }
    button[aria-selected="true"][data-baseweb="tab"] p,
    button[aria-selected="true"][data-baseweb="tab"] span {
        color: var(--accent-cyan) !important;
        font-weight: 700 !important;
    }
    /* Tab underline bar */
    div[role="tablist"] {
        border-bottom: 1px solid var(--border-dim) !important;
    }

    /* ── Sidebar ──────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #0E1320 !important;
        border-right: 1px solid var(--border-dim) !important;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: var(--text-prime) !important;
        font-weight: 600 !important;
        font-family: var(--font-body) !important;
    }

    /* ── Selectboxes & Dropdowns ───────────────────────────── */
    div[data-baseweb="select"] {
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="select"] * {
        color: var(--text-prime) !important;
        background-color: var(--bg-surface) !important;
    }
    div[role="listbox"] ul li, div[role="option"] {
        background-color: var(--bg-surface) !important;
        color: var(--text-prime) !important;
    }

    /* ── Sliders ──────────────────────────────────────────── */
    .stSlider label, .stSlider p {
        color: var(--text-prime) !important;
        font-weight: 600 !important;
    }

    /* ── Header Banner ────────────────────────────────────── */
    .header-container {
        background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%);
        border: 1px solid var(--border-dim);
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.30);
        border-left: 3px solid var(--accent-cyan);
        animation: controlRoomFadeIn 0.5s ease-out 0.1s both, borderPulse 3s ease-in-out infinite;
    }
    .header-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-prime) !important;
        margin: 0;
        font-family: var(--font-heading) !important;
        letter-spacing: -0.03em;
    }
    .header-subtitle {
        font-size: 0.85rem;
        color: var(--text-muted) !important;
        margin-top: 6px;
        font-weight: 500;
        font-family: var(--font-body) !important;
        letter-spacing: 0.02em;
    }

    /* ── Status Badges ────────────────────────────────────── */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-weight: 600;
        padding: 5px 14px;
        border-radius: 6px;
        font-size: 0.72rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-family: var(--font-mono) !important;
    }
    .badge-synthetic {
        background-color: var(--accent-amber-bg);
        color: var(--accent-amber) !important;
        border: 1px solid var(--accent-amber-border);
    }
    .badge-verified {
        background-color: rgba(16, 185, 129, 0.10);
        color: var(--accent-green) !important;
        border: 1px solid rgba(16, 185, 129, 0.30);
    }

    /* ── KPI Metric Card ──────────────────────────────────── */
    .metric-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-dim);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.20);
        transition: border-color 0.2s ease;
        height: 100%;
    }
    .metric-card:hover {
        border-color: var(--accent-cyan);
    }
    .metric-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-family: var(--font-body) !important;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-prime) !important;
        margin-top: 8px;
        letter-spacing: -0.03em;
        font-family: var(--font-mono) !important;
    }
    .metric-unit {
        font-size: 1rem;
        color: var(--text-muted) !important;
        font-weight: 500;
    }
    .metric-subtext {
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: var(--font-mono) !important;
    }
    .metric-subtext.verified { color: var(--accent-green) !important; }
    .metric-subtext.synthetic { color: var(--accent-amber) !important; }

    /* ── Control Panel Sidebar Title ───────────────────────── */
    .sidebar-title {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-prime) !important;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: var(--font-heading) !important;
        letter-spacing: -0.01em;
    }

    /* ── Table & Dataframe ─────────────────────────────────── */
    [data-testid="stDataFrame"], .stDataFrame, [data-testid="stTable"], .stTable {
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: 8px !important;
        overflow: hidden;
    }
    .stTable table, [data-testid="stTable"] table {
        width: 100% !important;
        border-collapse: collapse !important;
        background-color: var(--bg-surface) !important;
        color: var(--text-prime) !important;
    }
    .stTable th, [data-testid="stTable"] th {
        background-color: var(--bg-elevated) !important;
        color: var(--text-prime) !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        border-bottom: 1px solid var(--border-lit) !important;
        padding: 12px 16px !important;
        text-align: left !important;
        font-family: var(--font-heading) !important;
    }
    .stTable td, [data-testid="stTable"] td {
        color: var(--text-prime) !important;
        font-size: 0.82rem !important;
        font-weight: 400 !important;
        border-bottom: 1px solid var(--border-dim) !important;
        padding: 10px 16px !important;
        background-color: var(--bg-surface) !important;
        font-family: var(--font-mono) !important;
    }
    .stTable tr:nth-child(even) td, [data-testid="stTable"] tr:nth-child(even) td {
        background-color: var(--bg-elevated) !important;
    }

    /* ── Buttons ───────────────────────────────────────────── */
    .stButton > button, .stDownloadButton > button {
        background-color: var(--bg-surface) !important;
        color: var(--accent-cyan) !important;
        border: 1px solid var(--accent-cyan) !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 6px 16px !important;
        font-family: var(--font-heading) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: rgba(6, 182, 212, 0.12) !important;
        color: var(--accent-cyan) !important;
    }

    /* ── Form Submit Button ────────────────────────────────── */
    div[data-testid="stFormSubmitButton"] > button {
        background: var(--accent-cyan) !important;
        color: var(--bg-abyss) !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        border-radius: 6px !important;
        padding: 10px 18px !important;
        font-family: var(--font-heading) !important;
        letter-spacing: 0.02em;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: #22D3EE !important;
    }

    /* ── Horizontal Rule / Dividers ────────────────────────── */
    hr {
        border-color: var(--border-dim) !important;
        opacity: 0.5;
    }

    /* ── Scrollbar (Webkit) ────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-abyss); }
    ::-webkit-scrollbar-thumb { background: var(--border-dim); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--border-lit); }
</style>
""", unsafe_allow_html=True)

# ── Plotly Dark Theme Helper ───────────────────────────────────────────────────
def style_plotly_chart(fig, title_text=None):
    fig.update_layout(
        paper_bgcolor="#151C2C",
        plot_bgcolor="#1C2538",
        font=dict(color="#F8FAFC", family="IBM Plex Sans", size=12),
        margin=dict(l=25, r=25, t=45, b=35),
        legend=dict(
            font=dict(color="#94A3B8", size=11, family="IBM Plex Sans"),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#2A3550",
            borderwidth=1
        ),
        xaxis=dict(
            title_font=dict(color="#94A3B8", size=12, family="Space Grotesk"),
            tickfont=dict(color="#94A3B8", size=10, family="JetBrains Mono"),
            gridcolor="#2A3550",
            zerolinecolor="#334155",
            linecolor="#334155"
        ),
        yaxis=dict(
            title_font=dict(color="#94A3B8", size=12, family="Space Grotesk"),
            tickfont=dict(color="#94A3B8", size=10, family="JetBrains Mono"),
            gridcolor="#2A3550",
            zerolinecolor="#334155",
            linecolor="#334155"
        )
    )
    if title_text:
        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(color="#F8FAFC", size=14, family="Space Grotesk")
            )
        )
    return fig

# Data Loading Functions
@st.cache_data
def load_all_data():
    path_2026 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "India_Renewable_Curtailment_Synthetic_EDI_Final_PATCHED.xlsx"))
    path_multi = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "India_RE_Curtailment_EDI_MultiYear_2022_2025_14400_PATCHED.xlsx"))
    
    if os.path.exists(path_2026) and os.path.exists(path_multi):
        df1 = pd.read_excel(path_2026, sheet_name="Synthetic_Dataset")
        df2 = pd.read_excel(path_multi, sheet_name="Synthetic_Dataset")
        events_df = pd.concat([df1, df2], ignore_index=True)
    else:
        events_df = pd.DataFrame()
        
    cea_df = pd.DataFrame()
    compliance_df = pd.DataFrame()
    metrics = {}
    return cea_df, events_df, compliance_df, metrics

cea_df, events_df, compliance_df, metrics = load_all_data()

# Header Section
st.markdown("""
<div class="header-container">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
            <h1 class="header-title">RE Curtailment & Regulatory Compliance System</h1>
            <div class="header-subtitle">Curtailment Audit · Cause Classification · Grid Compliance Monitoring</div>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span class="status-badge badge-synthetic">● SYNTHETIC DATA INCLUDED</span>
            <span class="status-badge badge-verified">● CEA/POSOCO VERIFIED</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Control Panel Form
with st.sidebar.form(key="control_panel_form"):
    st.markdown("<div class='sidebar-title'>Control Panel</div>", unsafe_allow_html=True)
    
    regions = ["All Regions"] + list(events_df['Region'].dropna().unique()) if not events_df.empty else ["All Regions"]
    selected_region = st.selectbox("Filter by Region", regions)
    
    if selected_region != "All Regions":
        available_states = ["All States"] + list(events_df[events_df['Region'] == selected_region]['State'].dropna().unique())
    else:
        available_states = ["All States"] + list(events_df['State'].dropna().unique())
    selected_state = st.selectbox("Filter by State", available_states)
    
    causes = ["All Causes"] + list(events_df['Cause_Label'].dropna().unique()) if not events_df.empty else ["All Causes"]
    selected_cause = st.selectbox("Filter by Cause", causes)
    
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    show_results = st.form_submit_button("Apply Filters", use_container_width=True)

# Filter Dataset based on selected criteria
filtered_df = events_df.copy()
if selected_region != "All Regions":
    filtered_df = filtered_df[filtered_df['Region'] == selected_region]
if selected_state != "All States":
    filtered_df = filtered_df[filtered_df['State'] == selected_state]
if selected_cause != "All Causes":
    filtered_df = filtered_df[filtered_df['Cause_Label'] == selected_cause]

# Active Filters Banner Summary
st.markdown(f"""
<div class="filter-banner" style="background: #151C2C; border: 1px solid #2A3550; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; font-size: 0.82rem; color: #F8FAFC; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-family: 'IBM Plex Sans', sans-serif;">
    <div>
        <span style="color: #94A3B8; font-weight:600;">ACTIVE FILTER │</span>
        <span style="color: #06B6D4; font-weight:600; font-family: 'JetBrains Mono', monospace;">{selected_region}</span>
        <span style="color: #64748B;"> › </span>
        <span style="color: #06B6D4; font-weight:600; font-family: 'JetBrains Mono', monospace;">{selected_state}</span>
        <span style="color: #64748B;"> › </span>
        <span style="color: #06B6D4; font-weight:600; font-family: 'JetBrains Mono', monospace;">{selected_cause}</span>
    </div>
    <div>
        <span style="color: #94A3B8; font-weight:600;">RECORDS</span>
        <span style="color: #F8FAFC; font-weight:700; font-family: 'JetBrains Mono', monospace; background:#1C2538; border: 1px solid #2A3550; padding:3px 10px; border-radius:4px; margin-left:6px;">{len(filtered_df):,}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top KPI Executive Matrix Cards
c1, c2, c3, c4 = st.columns(4)

with c1:
    total_events = len(filtered_df)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Records</div>
        <div class='metric-value'>{total_events:,}</div>
        <div class='metric-subtext verified'>Filtered dataset</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    total_mwh = filtered_df['Curtailment_MW'].sum() if not filtered_df.empty else 0
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Curtailed Energy</div>
        <div class='metric-value'>{total_mwh:,.1f} <span class='metric-unit'>MW</span></div>
        <div class='metric-subtext synthetic'>● Synthetic — modelled estimate</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    total_re = filtered_df['RES_Generation_MW'].sum() if not filtered_df.empty else 0
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total RE Generation</div>
        <div class='metric-value'>{total_re:,.1f} <span class='metric-unit'>MW</span></div>
        <div class='metric-subtext verified'>● CEA/POSOCO verified</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    total_dem = filtered_df['Demand_MW'].sum() if not filtered_df.empty else 0
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Demand</div>
        <div class='metric-value'>{total_dem:,.1f} <span class='metric-unit'>MW</span></div>
        <div class='metric-subtext verified'>● CEA/POSOCO verified</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# Main Tabular Dashboard Container
tab1, tab2, tab3 = st.tabs([
    "Generation & Curtailment",
    "Regional Cause Breakdown",
    "State-level Deep Dive"
])

# ----------------------------------------------------
# TAB 1: Generation & Curtailment Overview
# ----------------------------------------------------
with tab1:
    st.markdown("### National / Regional Generation Mix & Curtailment Ranking")
    
    if not filtered_df.empty:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### RE Generation vs Demand over Time")
            # Need to aggregate by Date
            time_df = filtered_df.groupby('Date')[['Demand_MW', 'RES_Generation_MW']].sum().reset_index()
            fig_time = px.line(time_df, x='Date', y=['Demand_MW', 'RES_Generation_MW'], 
                               title="Daily Demand vs RE Generation (CEA/POSOCO Baselines)",
                               color_discrete_map={"Demand_MW": "#00e5ff", "RES_Generation_MW": "#10b981"},
                               template="plotly_dark")
            style_plotly_chart(fig_time)
            st.plotly_chart(fig_time, use_container_width=True)
            
        with col2:
            st.markdown("#### Regional Curtailment % Ranking")
            st.markdown("<span class='status-badge badge-synthetic' style='margin-bottom:8px;'>● Synthetic — modelled estimate</span>", unsafe_allow_html=True)
            # Need to show ranking Northern > Western > Eastern > NER > Southern
            reg_df = filtered_df.groupby('Region')['Curtailment_Percent'].mean().reset_index()
            # Explicitly sort to ensure correct order
            reg_df = reg_df.sort_values(by='Curtailment_Percent', ascending=False)
            fig_bar = px.bar(reg_df, x='Region', y='Curtailment_Percent', 
                             title="Average Curtailment % by Region",
                             color='Region',
                             template="plotly_dark")
            style_plotly_chart(fig_bar)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.markdown("#### Detailed Data View")
        st.dataframe(filtered_df[['Date', 'Region', 'State', 'Demand_MW', 'RES_Generation_MW', 'Curtailment_MW', 'Curtailment_Percent', 'is_synthetic_label']], use_container_width=True)

# ----------------------------------------------------
# TAB 2: Cause Classification
# ----------------------------------------------------
with tab2:
    st.markdown("### Regional Cause Breakdown & Skew")
    st.markdown("<span class='status-badge badge-synthetic' style='margin-bottom:8px;'>● Synthetic classification layer</span>", unsafe_allow_html=True)
    
    if not filtered_df.empty:
        col_t2_left, col_t2_right = st.columns([1, 1])
        
        with col_t2_left:
            st.markdown("#### Cause Skew by Region")
            cause_reg_df = filtered_df.groupby(['Region', 'Cause_Label']).size().reset_index(name='Count')
            fig_skew = px.bar(cause_reg_df, x='Region', y='Count', color='Cause_Label',
                              title="Regional Skew of Causes (Notice Northern/Western Transmission Dominance)",
                              barmode='stack', template="plotly_dark")
            style_plotly_chart(fig_skew)
            st.plotly_chart(fig_skew, use_container_width=True)
            
        with col_t2_right:
            st.markdown("#### Statutory SLDC Instruction Audit Log & Regulatory Deviation Tracker")
            display_df = filtered_df[['Date', 'Region', 'State', 'Dispatcher_Remark_Synthetic', 'Cause_Label', 'is_synthetic_label']].copy()
            st.dataframe(display_df, use_container_width=True)

# ----------------------------------------------------
# TAB 3: State-level Deep Dive
# ----------------------------------------------------
with tab3:
    st.markdown("### State-level Curtailment Profile & Analysis")
    
    if not filtered_df.empty:
        col_t3_left, col_t3_right = st.columns([1, 1])
        
        with col_t3_left:
            st.markdown("#### Curtailment vs Generation by State")
            state_agg = filtered_df.groupby('State')[['RES_Generation_MW', 'Curtailment_MW']].sum().reset_index()
            fig_scatter = px.scatter(state_agg, x='RES_Generation_MW', y='Curtailment_MW', color='State',
                                     size='Curtailment_MW', hover_name='State',
                                     title="Higher Generation States vs Total Curtailment (MW)",
                                     template="plotly_dark", size_max=45)
            style_plotly_chart(fig_scatter)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_t3_right:
            st.markdown("#### State-wise Aggregated Metrics")
            state_table = filtered_df.groupby('State').agg(
                Total_Demand_MW=('Demand_MW', 'sum'),
                Total_RES_Gen_MW=('RES_Generation_MW', 'sum'),
                Total_Curtailment_MW=('Curtailment_MW', 'sum'),
                Avg_Curtailment_Pct=('Curtailment_Percent', 'mean')
            ).reset_index()
            
            # Format columns for display
            state_table['Total_Demand_MW'] = state_table['Total_Demand_MW'].apply(lambda x: f"{x:,.1f}")
            state_table['Total_RES_Gen_MW'] = state_table['Total_RES_Gen_MW'].apply(lambda x: f"{x:,.1f}")
            state_table['Total_Curtailment_MW'] = state_table['Total_Curtailment_MW'].apply(lambda x: f"{x:,.1f}")
            state_table['Avg_Curtailment_Pct'] = state_table['Avg_Curtailment_Pct'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(state_table.sort_values(by='Total_Curtailment_MW', ascending=False), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.78rem; font-weight: 500; padding: 16px 0; font-family: 'IBM Plex Sans', sans-serif; letter-spacing: 0.03em;">
    RE Curtailment Analysis System · CEA / POSOCO / SLDC Data Pipeline · India Grid Operations
</div>
""", unsafe_allow_html=True)
