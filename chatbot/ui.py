"""
Streamlit UI Component for AI Energy Intelligence Assistant.
Harmonized with the Grid Control Room Dark Theme and existing dashboard styling.
"""

from typing import Dict, Any, Optional
import streamlit as pd_st
import streamlit as st
import pandas as pd

from chatbot.chatbot import EnergyChatbot
from chatbot.solar_calculator import calculate_solar_potential, STATE_TARIFF_MAP

def render_chatbot_tab(
    events_df: pd.DataFrame,
    compliance_df: Optional[pd.DataFrame] = None,
    active_filters: Optional[Dict[str, Any]] = None,
    classifier=None
):
    """
    Renders the dedicated AI Energy Intelligence Assistant tab.
    """
    # Initialize chatbot in st.session_state
    if "energy_chatbot" not in st.session_state:
        st.session_state.energy_chatbot = EnergyChatbot(classifier=classifier)
    elif classifier is not None and st.session_state.energy_chatbot.agent.classifier is None:
        st.session_state.energy_chatbot.agent.classifier = classifier

    bot: EnergyChatbot = st.session_state.energy_chatbot

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Chatbot Conversation Black Font Override
    st.markdown("""
    <style>
        /* All chatbot messages, content, headings, lists, bold text to black */
        [data-testid="stChatMessage"],
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div,
        [data-testid="stChatMessage"] label,
        [data-testid="stChatMessage"] h1,
        [data-testid="stChatMessage"] h2,
        [data-testid="stChatMessage"] h3,
        [data-testid="stChatMessage"] h4,
        [data-testid="stChatMessage"] h5,
        [data-testid="stChatMessage"] h6,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] ol,
        [data-testid="stChatMessage"] ul,
        [data-testid="stChatMessage"] strong,
        [data-testid="stChatMessage"] b,
        [data-testid="stChatMessage"] em,
        [data-testid="stChatMessage"] a,
        [data-testid="stChatMessage"] blockquote,
        [data-testid="stChatMessage"] blockquote *,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] *,
        [data-testid="stChatMessageContent"],
        [data-testid="stChatMessageContent"] *,
        .stChatMessage,
        .stChatMessage p,
        .stChatMessage span,
        .stChatMessage div,
        .stChatMessage * {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }

        /* Chatbot Expander & Table / Textual Outputs */
        [data-testid="stChatMessage"] [data-testid="stExpander"] summary,
        [data-testid="stChatMessage"] [data-testid="stExpander"] summary *,
        [data-testid="stChatMessage"] [data-testid="stExpander"] div,
        [data-testid="stChatMessage"] [data-testid="stExpander"] p,
        [data-testid="stChatMessage"] [data-testid="stExpander"] span,
        [data-testid="stChatMessage"] table,
        [data-testid="stChatMessage"] table *,
        [data-testid="stChatMessage"] th,
        [data-testid="stChatMessage"] td,
        [data-testid="stChatMessage"] [data-testid="stTable"] *,
        [data-testid="stChatMessage"] [data-testid="stDataFrame"] *,
        [data-testid="stChatMessage"] code,
        [data-testid="stChatMessage"] pre,
        [data-testid="stChatMessage"] pre * {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }

        /* Chat Input Text */
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input,
        [data-testid="stChatInputContainer"] textarea,
        div[data-baseweb="base-input"] textarea,
        .stChatInput textarea,
        .stChatInput input {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }

        /* Chat Input Placeholder */
        [data-testid="stChatInput"] textarea::placeholder,
        [data-testid="stChatInput"] input::placeholder,
        [data-testid="stChatInputContainer"] textarea::placeholder,
        div[data-baseweb="base-input"] textarea::placeholder,
        .stChatInput textarea::placeholder,
        .stChatInput input::placeholder {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            opacity: 0.65 !important;
        }

        /* ── Suggested Question Chips / Buttons (Black Font Override) ── */
        div[data-testid="column"] .stButton > button,
        div[data-testid="column"] .stButton > button *,
        div[data-testid="column"] .stButton > button p,
        div[data-testid="column"] .stButton > button span,
        div[data-testid="stHorizontalBlock"] .stButton > button,
        div[data-testid="stHorizontalBlock"] .stButton > button *,
        div[data-testid="stHorizontalBlock"] .stButton > button p,
        div[data-testid="stHorizontalBlock"] .stButton > button span,
        .stButton > button,
        .stButton > button *,
        .stButton > button p,
        .stButton > button span {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }

        .stButton > button:hover,
        .stButton > button:hover *,
        .stButton > button:hover p,
        .stButton > button:hover span {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Chatbot Header Banner
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #151C2C 0%, #1C2538 100%); border: 1px solid #2A3550; border-left: 3px solid #06B6D4; border-radius: 10px; padding: 18px 24px; margin-bottom: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <h2 style="margin: 0; font-size: 1.4rem; font-weight: 700; color: #F8FAFC; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em;">
                    🤖 AI Energy Intelligence Assistant
                </h2>
                <div style="color: #94A3B8; font-size: 0.82rem; margin-top: 4px; font-family: 'IBM Plex Sans', sans-serif;">
                    Data-Grounded Grid Analytics · NLP Cause Classification · Regulatory Auditing · Consumer Solar Advisory
                </div>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="status-badge badge-verified" style="font-size: 0.70rem;">● ZERO HALLUCINATION (PANDAS SOURCE OF TRUTH)</span>
                <span class="status-badge badge-synthetic" style="font-size: 0.70rem;">● {bot.provider_name.upper()}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Controls Bar: Scope & Sync Filter
    col_scope, col_sync, col_clear = st.columns([3, 2, 1])

    with col_sync:
        sync_active = st.checkbox(
            "Sync queries with Sidebar Filters", 
            value=True, 
            help="When checked, assistant queries inherit active Region, State, and Cause filters from the dashboard."
        )

    with col_scope:
        if sync_active and active_filters and any(v not in ["All Regions", "All States", "All Causes"] for v in active_filters.values()):
            scope_desc = f"Filter Scope: {active_filters.get('region', 'All')} › {active_filters.get('state', 'All')} › {active_filters.get('cause', 'All')}"
            scope_badge_class = "color: #06B6D4;"
        else:
            scope_desc = f"Filter Scope: Full Dataset ({len(events_df):,} records)"
            scope_badge_class = "color: #10B981;"

        st.markdown(f"""
        <div style="padding: 6px 12px; background: #151C2C; border: 1px solid #2A3550; border-radius: 6px; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; {scope_badge_class}">
            🔎 {scope_desc}
        </div>
        """, unsafe_allow_html=True)

    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            bot.clear_history()
            st.rerun()

    # Quick Suggestion Chips
    st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #000000 !important; margin-top: 10px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.05em;'>💡 Suggested Questions:</div>", unsafe_allow_html=True)
    
    suggested_cols = st.columns(4)
    preset_questions = [
        "Which state has the highest curtailment?",
        "What is the main cause of curtailment?",
        "Compare Western and Northern regions",
        "Show the monthly curtailment trend",
        "Classify remark: Emergency backing down to prevent grid failure at Bhadla",
        "How many records were flagged for compliance?",
        "Can I save money by installing rooftop solar?",
        "What is renewable energy curtailment?"
    ]

    selected_suggestion = None
    for i, q_text in enumerate(preset_questions):
        col_idx = i % 4
        with suggested_cols[col_idx]:
            if st.button(f"• {q_text[:32]}...", key=f"sugg_{i}", help=q_text, use_container_width=True):
                selected_suggestion = q_text

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # Chat Feed History Rendering
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_messages:
            st.markdown("""
            <div style="text-align: center; padding: 40px 20px; background: rgba(21, 28, 44, 0.5); border: 1px dashed #2A3550; border-radius: 10px; margin: 15px 0;">
                <div style="font-size: 2.2rem; margin-bottom: 10px;">⚡</div>
                <div style="font-size: 1rem; font-weight: 700; color: #000000 !important; font-family: 'Space Grotesk', sans-serif;">
                    How can I assist your grid analysis today?
                </div>
                <div style="font-size: 0.82rem; color: #000000 !important; max-width: 520px; margin: 8px auto 0 auto; line-height: 1.5; font-weight: 500;">
                    Ask statistical queries across 22,032 records, classify SLDC dispatcher remarks using NLP, 
                    audit regulatory compliance flags, or simulate household rooftop solar savings.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_messages:
                role = msg["role"]
                content = msg["content"]
                chart = msg.get("chart")
                table = msg.get("table")
                calc = msg.get("calculation")
                scope = msg.get("scope", "Dataset")

                with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "⚡"):
                    st.markdown(content)
                    
                    if role == "assistant":
                        # Render Plotly Chart if attached
                        if chart is not None:
                            st.plotly_chart(chart, use_container_width=True)

                        # Render Supporting Data Table if attached
                        if table is not None and not table.empty:
                            with st.expander("📋 View Supporting Data Table", expanded=False):
                                st.dataframe(table, use_container_width=True)

                        # Render Calculation Trace
                        if calc:
                            with st.expander("🧮 View Calculation & pandas Logic", expanded=False):
                                st.code(calc, language="text")

    # Chat Input Box
    user_input = st.chat_input("Ask anything about your energy data (e.g. Which state curtailed the most solar?)...")
    
    # Check if a suggestion was clicked or user typed
    query_to_run = selected_suggestion if selected_suggestion else user_input

    if query_to_run:
        # Append User Message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": query_to_run
        })

        # Process Query with DataAgent
        with st.spinner("Analyzing grid data..."):
            response_dict = bot.ask(
                query=query_to_run,
                df=events_df,
                compliance_df=compliance_df,
                active_filters=active_filters,
                sync_filters=sync_active
            )

        # Append Assistant Message
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response_dict["text"],
            "chart": response_dict.get("chart"),
            "table": response_dict.get("table"),
            "calculation": response_dict.get("calculation"),
            "scope": response_dict.get("scope")
        })

        st.rerun()

    # Interactive Rooftop Solar Calculator Widget in an Expander
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    with st.expander("☀️ Interactive Personal Rooftop Solar Calculator (Consumer Assistant)", expanded=False):
        st.markdown("""
        Estimate your household rooftop solar capacity, annual bill reduction, capital investment, 
        and government subsidies under the **PM Surya Ghar: Muft Bijli Yojana**.
        """)
        
        calc_c1, calc_c2, calc_c3 = st.columns(3)
        with calc_c1:
            monthly_consumption = st.number_input("Monthly Consumption (kWh / Units)", min_value=50.0, max_value=3000.0, value=300.0, step=25.0)
        with calc_c2:
            calc_state = st.selectbox("Location / State", options=list(STATE_TARIFF_MAP.keys()), index=0)
        with calc_c3:
            roof_sqft = st.number_input("Available Shadow-Free Roof Area (sq. ft.)", min_value=50.0, max_value=10000.0, value=400.0, step=50.0)

        if st.button("Calculate Solar Estimate", key="btn_calc_solar"):
            solar_res = calculate_solar_potential(
                monthly_units=monthly_consumption,
                state=calc_state,
                rooftop_sqft=roof_sqft
            )
            st.markdown(solar_res["summary_markdown"], unsafe_allow_html=True)
            with st.expander("🧮 View Detailed Step-by-Step Mathematical Formulation"):
                st.code(solar_res["calculation_steps"], language="text")
