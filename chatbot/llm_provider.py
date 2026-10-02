"""
LLM Provider Abstraction & Deterministic Natural Language Generator.
Provides seamless fallback to deterministic template-driven NLG when no API key is configured.
"""

import os
import json
from typing import Dict, Any, Optional
from chatbot.prompts import LLM_SYSTEM_PROMPT, DOMAIN_DEFINITIONS, CONSUMER_TIPS, DISCLAIMER_SYNTHETIC, DISCLAIMER_UNAVAILABLE

class LLMProvider:
    def __init__(self):
        self.provider_name = "Deterministic (Offline Engine)"
        self.api_key = None
        self.client = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Detects available environment variables for OpenAI, Gemini, or Groq."""
        # 1. Check OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                self.api_key = openai_key
                self.provider_name = "OpenAI (GPT-4o-mini)"
                self.client = openai.OpenAI(api_key=openai_key)
                return
            except Exception:
                pass

        # 2. Check Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self.api_key = gemini_key
                self.provider_name = "Google Gemini"
                self.client = genai.GenerativeModel("gemini-1.5-flash")
                return
            except Exception:
                pass

        # 3. Check Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import Groq
                self.api_key = groq_key
                self.provider_name = "Groq (Llama-3)"
                self.client = Groq(api_key=groq_key)
                return
            except Exception:
                pass

    def is_llm_active(self) -> bool:
        """Returns True if a live remote LLM is initialized."""
        return self.client is not None

    def generate_response(
        self,
        query: str,
        facts_payload: Dict[str, Any],
        intent: str
    ) -> str:
        """
        Generates an authoritative natural language answer.
        If an LLM is active, sends the pre-computed facts payload to the LLM.
        Otherwise, uses the Deterministic NLG engine.
        """
        # If payload indicates an error or unavailable data, return directly
        if "error" in facts_payload:
            return f"⚠️ {facts_payload['error']}"

        # If live LLM is configured, call it with strict factual grounding
        if self.is_llm_active():
            try:
                prompt_text = (
                    f"User Question: {query}\n\n"
                    f"Intent: {intent}\n\n"
                    f"PRE-CALCULATED FACTS (DO NOT INVENT NUMBERS):\n"
                    f"{json.dumps(facts_payload, default=str, indent=2)}\n\n"
                    f"Provide a clear, professional, data-grounded response citing these actual numbers."
                )
                if "OpenAI" in self.provider_name:
                    resp = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": LLM_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt_text}
                        ],
                        temperature=0.2,
                        max_tokens=400
                    )
                    return resp.choices[0].message.content.strip()
                elif "Gemini" in self.provider_name:
                    resp = self.client.generate_content(f"{LLM_SYSTEM_PROMPT}\n\n{prompt_text}")
                    return resp.text.strip()
                elif "Groq" in self.provider_name:
                    resp = self.client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": LLM_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt_text}
                        ],
                        temperature=0.2,
                        max_tokens=400
                    )
                    return resp.choices[0].message.content.strip()
            except Exception as e:
                # Graceful fallback to Deterministic NLG if API call fails
                pass

        # Deterministic NLG Generator
        return self._deterministic_nlg(query, facts_payload, intent)

    def _deterministic_nlg(
        self,
        query: str,
        payload: Dict[str, Any],
        intent: str
    ) -> str:
        """Formats the calculated payload into clean, executive markdown."""
        scope = payload.get("scope", "Current Dataset")

        # 1. Dataset Overview / Summary
        if intent == "INTENT_DATA_SUMMARY":
            return (
                f"### ⚡ Indian Renewable Energy Curtailment & Grid Compliance Overview\n\n"
                f"According to the loaded dataset ({payload.get('date_range', 'N/A')}):\n\n"
                f"• **Total Recorded Events**: **{payload.get('total_records', 0):,}**\n"
                f"• **Total Curtailed Energy**: **{payload.get('total_curtailment_mw', 0):,.1f} MW**\n"
                f"• **Average Curtailment per Event**: **{payload.get('avg_curtailment_mw', 0):,.1f} MW** (Peak: {payload.get('max_curtailment_mw', 0):,.1f} MW)\n"
                f"• **Total Renewable Generation**: **{payload.get('total_re_gen_mw', 0):,.1f} MW**\n"
                f"• **Total Grid Demand**: **{payload.get('total_demand_mw', 0):,.1f} MW**\n"
                f"• **Average Curtailment %**: **{payload.get('avg_curtailment_pct', 0):.2f}%**\n"
                f"• **Geographic Coverage**: **{payload.get('states_count', 0)} States** across **{payload.get('regions_count', 0)} Regional Grids**\n\n"
                f"*(Demand & Generation figures verified against CEA/POSOCO baselines; curtailment figures are synthetic modeled estimates.)*"
            )

        # 2. Metric Statistic
        if intent == "INTENT_METRIC_STAT":
            stat = payload.get("stat_type", "value")
            col = payload.get("column", "Metric")
            val = payload.get("value", 0.0)
            cnt = payload.get("count", 0)

            unit = "MW" if "MW" in col else ("%" if "Percent" in col else "")
            stat_name = {
                "mean": "average",
                "sum": "total",
                "max": "highest recorded",
                "min": "lowest recorded",
                "median": "median",
                "std": "standard deviation of",
                "count": "total count of"
            }.get(stat, stat)

            return (
                f"Based on the current dataset (**{scope}**), the **{stat_name} {col}** is **{val:,.2f} {unit}** "
                f"(calculated across {cnt:,} observations).\n\n"
                f"📊 **Metric**: `{col}`  \n"
                f"🔎 **Scope**: `{scope}`  \n"
                f"📈 **Calculated Result**: **{val:,.2f} {unit}**"
            )

        # 3. Macro Curtailment Percentage
        if intent == "INTENT_CURTAILMENT_PERCENTAGE":
            return (
                f"Based on the current dataset (**{scope}**):\n\n"
                f"• **Average Record Curtailment %**: **{payload.get('mean_record_curtailment_pct', 0):.2f}%**\n"
                f"• **Total Curtailed Energy**: **{payload.get('total_curtailment_mw', 0):,.1f} MW**\n"
                f"• **Total RE Generation**: **{payload.get('total_re_generation_mw', 0):,.1f} MW**\n"
                f"• **Total Potential RE Generation**: **{payload.get('total_potential_re_mw', 0):,.1f} MW**\n"
                f"• **Macro Curtailment Share of Potential RE**: **{payload.get('macro_curtailment_share_pct', 0):.2f}%**\n\n"
                f"💡 *Interpretation*: Out of {payload.get('total_potential_re_mw', 0):,.1f} MW of available renewable energy, "
                f"{payload.get('macro_curtailment_share_pct', 0):.2f}% was curtailed due to system constraints."
            )

        # 4. Top N / Ranking
        if intent == "INTENT_RANKING":
            dir_str = payload.get("direction", "Top")
            n = payload.get("n", 5)
            col = payload.get("group_col", "State")
            m_col = payload.get("metric_col", "Curtailment_MW")
            agg = payload.get("agg", "sum")
            top_e = payload.get("top_entity", "None")
            top_v = payload.get("top_value", 0.0)

            unit = "MW" if "MW" in m_col else ("%" if "Percent" in m_col else "")
            rows_str = ""
            for item in payload.get("rankings", []):
                rows_str += f"{item['rank']}. **{item['entity']}**: {item['value']:,.2f} {unit}\n"

            return (
                f"Based on the current dataset (**{scope}**), **{top_e}** has the **{dir_str.lower()} {agg} {m_col}** "
                f"at **{top_v:,.2f} {unit}**.\n\n"
                f"### 🏆 {dir_str} {n} {col}s by {m_col} ({agg.capitalize()}):\n"
                f"{rows_str}\n"
                f"🔎 **Scope**: `{scope}`"
            )

        # 5. Entity Comparison (State vs State or Region vs Region)
        if intent == "INTENT_COMPARISON":
            e1 = payload.get("entity1", "Entity 1")
            v1 = payload.get("val1", 0.0)
            e2 = payload.get("entity2", "Entity 2")
            v2 = payload.get("val2", 0.0)
            m = payload.get("metric_col", "Curtailment_MW")
            agg = payload.get("agg", "mean")
            diff = payload.get("abs_diff", 0.0)
            pct = payload.get("pct_diff", 0.0)
            interp = payload.get("interpretation", "")

            unit = "MW" if "MW" in m else ("%" if "Percent" in m else "")
            return (
                f"### ⚖️ Comparison: {e1} vs {e2}\n\n"
                f"• **{e1}**: {agg.capitalize()} {m} = **{v1:,.2f} {unit}** ({payload.get('count1', 0):,} records)\n"
                f"• **{e2}**: {agg.capitalize()} {m} = **{v2:,.2f} {unit}** ({payload.get('count2', 0):,} records)\n"
                f"• **Absolute Difference**: **{diff:,.2f} {unit}**\n"
                f"• **Percentage Difference**: **{pct:.1f}%**\n\n"
                f"💡 **Takeaway**: {interp}\n\n"
                f"🔎 **Scope**: `{scope}`"
            )

        # 6. Time Series / Trend
        if intent == "INTENT_TIME_TREND":
            m = payload.get("metric_col", "Curtailment_MW")
            agg = payload.get("agg", "sum")
            peak_p = payload.get("peak_period", "N/A")
            peak_v = payload.get("peak_value", 0.0)
            low_p = payload.get("lowest_period", "N/A")
            low_v = payload.get("lowest_value", 0.0)

            unit = "MW" if "MW" in m else ("%" if "Percent" in m else "")
            return (
                f"### 📈 Historical Trend Analysis for {m} ({agg.capitalize()})\n\n"
                f"Across **{payload.get('periods_count', 0)} monthly intervals** in the dataset:\n\n"
                f"• **Peak Curtailment Month**: **{peak_p}** with **{peak_v:,.1f} {unit}**\n"
                f"• **Lowest Curtailment Month**: **{low_p}** with **{low_v:,.1f} {unit}**\n\n"
                f"💡 *Curtailment in India strongly peaks during high-wind monsoon months (June–August) "
                f"and clear-sky pre-monsoon solar surges (April–May).*\n\n"
                f"🔎 **Scope**: `{scope}`"
            )

        # 7. Cause Distribution
        if intent == "INTENT_CAUSE_ANALYSIS":
            primary = payload.get("primary_cause", "N/A")
            p_cnt = payload.get("primary_count", 0)
            p_pct = payload.get("primary_pct", 0.0)

            dist_lines = ""
            for cause_name, info in payload.get("distribution", {}).items():
                dist_lines += f"• **{cause_name}**: {info['pct']:.1f}% ({info['count']:,} events)\n"

            return (
                f"Based on the current dataset (**{scope}**), **{primary}** is the most frequent cause of curtailment, "
                f"accounting for **{p_pct:.1f}%** ({p_cnt:,} events).\n\n"
                f"### 📊 Cause Distribution Breakdown:\n"
                f"{dist_lines}\n"
                f"💡 *Transmission Constraint and Grid Security dominate inter-state RE corridors, "
                f"highlighting evacuation bottlenecks between major solar/wind parks and regional load centers.*"
            )

        # 8. Specific Cause Query
        if intent == "INTENT_CAUSE_SPECIFIC":
            return (
                f"Based on the current dataset (**{scope}**):\n\n"
                f"The cause **{payload.get('cause', 'N/A')}** occurs in **{payload.get('count', 0):,} records** "
                f"({payload.get('percentage', 0):.2f}% of events in this scope)."
            )

        # 9. Correlation
        if intent == "INTENT_CORRELATION":
            return (
                f"### 🔗 Statistical Correlation Analysis\n\n"
                f"• **Variables**: `{payload.get('col1')}` vs `{payload.get('col2')}`\n"
                f"• **Pearson Correlation Coefficient (r)**: **{payload.get('r', 0):.4f}**\n"
                f"• **Sample Size**: **{payload.get('sample_size', 0):,} records**\n\n"
                f"💡 **Interpretation**: {payload.get('interpretation')}\n\n"
                f"🔎 **Scope**: `{scope}`"
            )

        # 10. Dispatcher Remark Keyword Search
        if intent == "INTENT_REMARK_SEARCH":
            kw = payload.get("keyword", "")
            matches = payload.get("total_matches", 0)
            return (
                f"Found **{matches:,} dispatcher remarks** containing the term '**{kw}**' in the current scope (**{scope}**).\n\n"
                f"Sample records are listed in the supporting table below."
            )

        # 11. ML Cause Prediction
        if intent == "INTENT_ML_PREDICT":
            cause = payload.get("predicted_cause", "Unknown")
            conf = payload.get("confidence_pct", 0.0)
            status = payload.get("pipeline_status", "classified")
            review_note = "⚠️ *Low confidence (< 60.0%) — flagged for human operator review (Brain Rule 3).*" if payload.get("needs_review") else "✅ *High confidence classification.*"

            probs_str = ""
            for c_name, c_prob in payload.get("all_probabilities", {}).items():
                probs_str += f"• {c_name}: **{c_prob:.1f}%**\n"

            return (
                f"### 🤖 NLP Curtailment Cause Prediction\n\n"
                f"**Input Remark**: *\"{payload.get('remark')}\"*\n\n"
                f"• **Predicted Primary Cause**: **{cause}**  \n"
                f"• **Model Confidence Score**: **{conf:.1f}%**  \n"
                f"• **Pipeline Status**: `{status}` ({review_note})  \n\n"
                f"**Full Probability Distribution**:\n"
                f"{probs_str}\n"
                f"> ℹ️ *Note: This prediction is generated by the trained Scikit-Learn TF-IDF + Logistic Regression pipeline. "
                f"ML predictions represent probabilistic classifications based on historical remark vocabulary, not statutory SLDC determinations.*"
            )

        # 12. Regulatory Compliance Summary
        if intent == "INTENT_COMPLIANCE":
            return (
                f"### 🛡️ Regulatory Compliance & Audit Scorecard (Agent 4 - Warden)\n\n"
                f"Evaluated against CERC/IEGC disclosure standards:\n\n"
                f"• **Total Audited Entities**: **{payload.get('total_audited_regions', 0)} regions/states**\n"
                f"• **Average Composite Compliance Score**: **{payload.get('avg_composite_score', 0):.1f} / 100**\n"
                f"• **Audit Discrepancies & Flagged Records**: **{payload.get('total_flagged_events', 0):,} events**\n\n"
                f"Records are flagged if generation deviation (|ΔG - Curtailed|) exceeds 5 MW (Rule 1 mismatch) "
                f"or if classification confidence falls below 60% (Rule 3).\n\n"
                f"Review the flagged audit logs in the table below."
            )

        # 13. General Definitions
        if intent.startswith("INTENT_GENERAL_QA_"):
            def_key = intent.replace("INTENT_GENERAL_QA_", "").lower()
            return DOMAIN_DEFINITIONS.get(def_key, DOMAIN_DEFINITIONS["curtailment"])

        # 14. Consumer Guidance
        if intent == "INTENT_CONSUMER_REDUCE_BILL":
            return CONSUMER_TIPS["reduce_bill"]
        if intent == "INTENT_CONSUMER_SOLAR_BENEFITS":
            return CONSUMER_TIPS["solar_benefits"]
        if intent == "INTENT_CONSUMER_GRID_IMPACT":
            return CONSUMER_TIPS["solar_grid_impact"]
        if intent == "INTENT_CONSUMER_PEAK_RE":
            return CONSUMER_TIPS["when_is_re_peak"]

        # 15. Solar Calculator Result
        if intent == "INTENT_SOLAR_CALCULATOR":
            return payload.get("summary_markdown", "Solar calculation completed.")

        # Fallback
        return DISCLAIMER_UNAVAILABLE
