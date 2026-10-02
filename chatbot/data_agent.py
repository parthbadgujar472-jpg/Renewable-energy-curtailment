"""
DataAgent: Orchestrator connecting Query Parsing, Analytics Execution,
Context Management, and Response Synthesis.
"""

from typing import Dict, Any, Optional, Tuple
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from chatbot.query_parser import extract_entities, classify_intent
from chatbot.context import ConversationContext
from chatbot.analytics import (
    get_dataset_summary,
    get_column_stat,
    get_curtailment_percentage_analysis,
    get_top_n,
    compare_entities,
    compare_metrics,
    time_series_analysis,
    cause_analysis,
    correlation_analysis,
    search_remarks,
    predict_remark_cause,
    compliance_analysis,
    apply_filters
)
from chatbot.solar_calculator import calculate_solar_potential
from chatbot.llm_provider import LLMProvider
from chatbot.prompts import DISCLAIMER_UNAVAILABLE

def style_agent_chart(fig: go.Figure, title_text: Optional[str] = None) -> go.Figure:
    """Applies the Control Room Dark Theme to generated Plotly figures."""
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

class DataAgent:
    def __init__(self, classifier=None):
        self.classifier = classifier
        self.llm_provider = LLMProvider()

    def process_query(
        self,
        query: str,
        df: pd.DataFrame,
        compliance_df: Optional[pd.DataFrame] = None,
        context: Optional[ConversationContext] = None,
        active_filters: Optional[Dict[str, Any]] = None,
        sync_filters: bool = True
    ) -> Dict[str, Any]:
        """
        Main query processing pipeline:
        1. Contextual reference resolution (pronouns, ellipses)
        2. Intent classification & entity extraction
        3. Controlled Python / Pandas analytics execution
        4. Visualization & data table generation
        5. Natural language response synthesis
        6. Context state update
        """
        if context is None:
            context = ConversationContext()

        if compliance_df is None:
            compliance_df = pd.DataFrame()

        # Step 1: Initial Entity Extraction
        raw_entities = extract_entities(query)

        # Step 2: Context Reference Resolution (e.g. 'its demand', 'which one is higher?')
        resolved_query, entities = context.resolve_references(query, raw_entities)

        # Step 3: Intent Classification
        intent = classify_intent(resolved_query, entities)

        # Build execution filter dictionary
        exec_filters: Dict[str, Any] = {}
        if sync_filters and active_filters:
            if active_filters.get("region") and active_filters["region"] != "All Regions":
                exec_filters["region"] = active_filters["region"]
            if active_filters.get("state") and active_filters["state"] != "All States":
                exec_filters["state"] = active_filters["state"]
            if active_filters.get("cause") and active_filters["cause"] != "All Causes":
                exec_filters["cause"] = active_filters["cause"]

        # Override with explicit entities extracted from user query
        if entities.get("states"):
            if len(entities["states"]) == 1:
                exec_filters["state"] = entities["states"][0]
        if entities.get("regions"):
            if len(entities["regions"]) == 1:
                exec_filters["region"] = entities["regions"][0]
        if entities.get("cause"):
            exec_filters["cause"] = entities["cause"]
        if entities.get("year"):
            exec_filters["year"] = entities["year"]
        if entities.get("month"):
            exec_filters["month"] = entities["month"]
        if entities.get("quarter"):
            exec_filters["quarter"] = entities["quarter"]
        if entities.get("season"):
            exec_filters["season"] = entities["season"]

        payload: Dict[str, Any] = {}
        chart_fig: Optional[go.Figure] = None
        table_df: Optional[pd.DataFrame] = None
        calc_steps: Optional[str] = None

        # Step 4: Analytical Routing
        if intent == "INTENT_DATA_SUMMARY":
            payload = get_dataset_summary(df)
            calc_steps = payload.get("calculation")

        elif intent == "INTENT_METRIC_STAT":
            metric = entities.get("metric") or "Curtailment_MW"
            stat_type = entities.get("stat_type") or "mean"
            payload = get_column_stat(df, column=metric, stat_type=stat_type, filters=exec_filters)
            calc_steps = payload.get("calculation")

        elif intent == "INTENT_CURTAILMENT_PERCENTAGE":
            payload = get_curtailment_percentage_analysis(df, filters=exec_filters)
            calc_steps = payload.get("calculation")

        elif intent == "INTENT_RANKING":
            group_col = "Region" if "region" in resolved_query.lower() and "state" not in resolved_query.lower() else "State"
            metric = entities.get("metric") or "Curtailment_MW"
            top_n = entities.get("top_n", 5)
            ascending = "lowest" in resolved_query.lower() or "least" in resolved_query.lower()
            agg = "mean" if "average" in resolved_query.lower() or "mean" in resolved_query.lower() else "sum"

            payload = get_top_n(
                df, group_col=group_col, metric_col=metric, n=top_n, 
                ascending=ascending, agg=agg, filters=exec_filters
            )
            calc_steps = payload.get("calculation")
            if "table_df" in payload and not payload["table_df"].empty:
                table_df = payload["table_df"]
                # Create ranking bar chart
                fig = px.bar(
                    table_df, x=group_col, y=metric, 
                    title=f"{payload.get('direction', 'Top')} {top_n} {group_col}s by {metric}",
                    color=group_col, template="plotly_dark"
                )
                chart_fig = style_agent_chart(fig)

        elif intent == "INTENT_COMPARISON":
            metric = entities.get("metric") or "Curtailment_MW"
            agg = "sum" if "total" in resolved_query.lower() or "sum" in resolved_query.lower() else "mean"

            if len(entities.get("states", [])) >= 2:
                payload = compare_entities(
                    df, group_col="State", entity1=entities["states"][0], entity2=entities["states"][1],
                    metric_col=metric, agg=agg, filters=exec_filters
                )
            elif len(entities.get("regions", [])) >= 2:
                payload = compare_entities(
                    df, group_col="Region", entity1=entities["regions"][0], entity2=entities["regions"][1],
                    metric_col=metric, agg=agg, filters=exec_filters
                )
            else:
                # Compare metrics (e.g. demand vs RE generation)
                payload = compare_metrics(
                    df, metrics=["Demand_MW", "RES_Generation_MW", "Curtailment_MW"],
                    agg=agg, filters=exec_filters
                )

            calc_steps = payload.get("calculation")
            if "table_df" in payload and not payload["table_df"].empty:
                table_df = payload["table_df"]
                x_col = table_df.columns[0]
                y_col = table_df.columns[1]
                fig = px.bar(
                    table_df, x=x_col, y=y_col, color=x_col,
                    title=f"Comparison: {x_col} by {y_col}", template="plotly_dark"
                )
                chart_fig = style_agent_chart(fig)

        elif intent == "INTENT_TIME_TREND":
            metric = entities.get("metric") or "Curtailment_MW"
            agg = "sum" if "total" in resolved_query.lower() or "sum" in resolved_query.lower() else "sum"
            payload = time_series_analysis(df, metric_col=metric, agg=agg, freq="M", filters=exec_filters)
            calc_steps = payload.get("calculation")
            if "time_series_df" in payload and not payload["time_series_df"].empty:
                ts_df = payload["time_series_df"]
                fig = px.line(
                    ts_df, x="Period", y=metric,
                    title=f"Monthly Trend: {metric} ({agg.capitalize()})",
                    template="plotly_dark",
                    color_discrete_sequence=["#06B6D4"]
                )
                chart_fig = style_agent_chart(fig)

        elif intent == "INTENT_CAUSE_ANALYSIS":
            payload = cause_analysis(df, filters=exec_filters)
            calc_steps = payload.get("calculation")
            if "table_df" in payload and not payload["table_df"].empty:
                table_df = payload["table_df"]
                fig = px.pie(
                    table_df, names="Cause_Label", values="Count",
                    title="Curtailment Cause Distribution",
                    template="plotly_dark",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Tealgrn
                )
                chart_fig = style_agent_chart(fig)

        elif intent == "INTENT_CAUSE_SPECIFIC":
            c_name = entities.get("cause")
            full_cause_analysis = cause_analysis(df, filters=exec_filters)
            dist = full_cause_analysis.get("distribution", {})
            c_info = dist.get(c_name, {"count": 0, "pct": 0.0})
            payload = {
                "cause": c_name,
                "count": c_info["count"],
                "percentage": c_info["pct"],
                "scope": full_cause_analysis.get("scope", "Current Dataset"),
                "calculation": f"Filtered records with Cause_Label == '{c_name}' -> {c_info['count']} matches."
            }
            calc_steps = payload.get("calculation")

        elif intent == "INTENT_CORRELATION":
            col1 = "Demand_MW"
            col2 = "Curtailment_MW"
            if entities.get("metric") and entities["metric"] != "Curtailment_MW":
                col1 = entities["metric"]
            payload = correlation_analysis(df, col1=col1, col2=col2, filters=exec_filters)
            calc_steps = payload.get("calculation")

        elif intent == "INTENT_REMARK_SEARCH":
            # Extract keyword
            kw_match = re.search(r"(?:mentioning|containing|about|with|for)\s+([a-zA-Z0-9_\-\s]+)", resolved_query, re.IGNORECASE)
            keyword = kw_match.group(1).strip() if kw_match else "overloading"
            payload = search_remarks(df, keyword=keyword, limit=8, filters=exec_filters)
            calc_steps = payload.get("calculation")
            if "table_df" in payload and not payload["table_df"].empty:
                display_cols = [c for c in ["Date", "State", "Region", "Dispatcher_Remark_Synthetic", "Cause_Label"] if c in payload["table_df"].columns]
                table_df = payload["table_df"][display_cols]

        elif intent == "INTENT_ML_PREDICT":
            # Extract remark text from query
            remark_text = resolved_query
            if ":" in resolved_query:
                remark_text = resolved_query.split(":", 1)[1].strip()
            elif "remark" in resolved_query.lower():
                r_match = re.search(r"remark\s+(?:is|as)?\s*[\"']?([^\"']+)[\"']?", resolved_query, re.IGNORECASE)
                if r_match:
                    remark_text = r_match.group(1).strip()
            payload = predict_remark_cause(remark_text, classifier=self.classifier)
            calc_steps = payload.get("calculation")

        elif intent == "INTENT_COMPLIANCE":
            payload = compliance_analysis(compliance_df, events_df=df)
            calc_steps = payload.get("calculation")
            if "compliance_scorecard_df" in payload and not payload["compliance_scorecard_df"].empty:
                table_df = payload["compliance_scorecard_df"]

        elif intent == "INTENT_SOLAR_CALCULATOR":
            units = entities.get("solar_units") or 300.0
            sqft = entities.get("solar_sqft")
            st_name = entities.get("states")[0] if entities.get("states") else None
            payload = calculate_solar_potential(monthly_units=units, state=st_name, rooftop_sqft=sqft)
            calc_steps = payload.get("calculation_steps")

        elif intent.startswith("INTENT_GENERAL_QA_") or intent.startswith("INTENT_CONSUMER_"):
            payload = {"scope": "General Energy Domain"}

        elif intent == "INTENT_CHART":
            # Generate a visualization based on context
            metric = context.last_metric or "Curtailment_MW"
            payload = time_series_analysis(df, metric_col=metric, agg="sum", freq="M", filters=exec_filters)
            calc_steps = payload.get("calculation")
            if "time_series_df" in payload and not payload["time_series_df"].empty:
                ts_df = payload["time_series_df"]
                fig = px.line(
                    ts_df, x="Period", y=metric,
                    title=f"Visualization: {metric} over Time",
                    template="plotly_dark",
                    color_discrete_sequence=["#06B6D4"]
                )
                chart_fig = style_agent_chart(fig)

        else:
            payload = {"error": DISCLAIMER_UNAVAILABLE}

        # Step 5: Synthesize Natural Language Response
        text_response = self.llm_provider.generate_response(
            query=resolved_query,
            facts_payload=payload,
            intent=intent
        )

        # Step 6: Update Context
        context.update_from_entities(entities, intent=intent, payload=payload)
        context.add_message(
            role="user",
            content=query
        )
        context.add_message(
            role="assistant",
            content=text_response,
            metadata={
                "intent": intent,
                "scope": payload.get("scope", "Full Dataset"),
                "has_chart": chart_fig is not None,
                "has_table": table_df is not None,
                "has_calc": calc_steps is not None
            }
        )

        return {
            "text": text_response,
            "chart": chart_fig,
            "table": table_df,
            "calculation": calc_steps,
            "scope": payload.get("scope", "Full Dataset"),
            "intent": intent,
            "resolved_query": resolved_query,
            "entities": entities
        }
