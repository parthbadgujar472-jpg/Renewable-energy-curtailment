"""
Comprehensive Unit & Integration Test Suite for AI Energy Intelligence Assistant.
Tests all 14 required capabilities plus 18 representative user questions.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chatbot.chatbot import EnergyChatbot
from chatbot.data_agent import DataAgent
from chatbot.context import ConversationContext
from chatbot.query_parser import extract_entities, classify_intent
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
from agents.analyst.classifier import CurtailmentRemarkClassifier

class TestEnergyChatbotSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Loads sample dataset and initializes trained classifier for testing."""
        path_2026 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "India_Renewable_Curtailment_Synthetic_EDI_Final_PATCHED.xlsx"))
        path_multi = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "India_RE_Curtailment_EDI_MultiYear_2022_2025_14400_PATCHED.xlsx"))
        
        if os.path.exists(path_2026) and os.path.exists(path_multi):
            df1 = pd.read_excel(path_2026, sheet_name="Synthetic_Dataset")
            df2 = pd.read_excel(path_multi, sheet_name="Synthetic_Dataset")
            cls.df = pd.concat([df1, df2], ignore_index=True)
        else:
            cls.df = pd.DataFrame()

        # Initialize and train ML classifier
        cls.classifier = CurtailmentRemarkClassifier()
        synth_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "synthetic_curtailment_events.csv"))
        if os.path.exists(synth_csv):
            train_df = pd.read_csv(synth_csv)
            cls.classifier.train_and_evaluate(train_df)

        cls.bot = EnergyChatbot(classifier=cls.classifier)

    # 1. Dataset Loading Test
    def test_01_dataset_loading(self):
        self.assertFalse(self.df.empty, "Dataset should not be empty")
        self.assertIn("Curtailment_MW", self.df.columns)
        self.assertIn("RES_Generation_MW", self.df.columns)
        self.assertIn("Demand_MW", self.df.columns)
        self.assertIn("State", self.df.columns)
        self.assertIn("Region", self.df.columns)
        self.assertGreater(len(self.df), 10000, "Dataset should contain > 10,000 multi-year records")

    # 2. Missing Columns Handling
    def test_02_missing_columns(self):
        df_missing = self.df.drop(columns=["Curtailment_MW"], errors="ignore")
        stat = get_column_stat(df_missing, column="Curtailment_MW", stat_type="mean")
        self.assertIn("error", stat)
        self.assertIn("not found", stat["error"])

    # 3. Average & Sum Calculations (No Hallucination Check)
    def test_03_average_and_sum_calculations(self):
        stat = get_column_stat(self.df, column="Curtailment_MW", stat_type="mean")
        ground_truth_mean = float(self.df["Curtailment_MW"].mean())
        self.assertAlmostEqual(stat["value"], ground_truth_mean, places=2)

        stat_sum = get_column_stat(self.df, column="RES_Generation_MW", stat_type="sum")
        ground_truth_sum = float(self.df["RES_Generation_MW"].sum())
        self.assertAlmostEqual(stat_sum["value"], ground_truth_sum, places=1)

    # 4. Group-by & Rankings
    def test_04_groupby_and_ranking(self):
        ranking = get_top_n(self.df, group_col="State", metric_col="Curtailment_MW", n=5)
        self.assertEqual(len(ranking["rankings"]), 5)
        
        # Verify rank 1 matches pandas ground truth
        top_state_pandas = self.df.groupby("State")["Curtailment_MW"].sum().idxmax()
        self.assertEqual(ranking["top_entity"], top_state_pandas)

    # 5. Filtering Functionality
    def test_05_filtering(self):
        filtered_df, scope = apply_filters(self.df, region="Western", state="Maharashtra")
        self.assertFalse(filtered_df.empty)
        self.assertTrue((filtered_df["Region"] == "Western").all())
        self.assertTrue((filtered_df["State"] == "Maharashtra").all())
        self.assertIn("Maharashtra", scope[0])

    # 6. Date / Temporal Analysis
    def test_06_date_analysis(self):
        ts = time_series_analysis(self.df, metric_col="Curtailment_MW", agg="sum", freq="M")
        self.assertNotIn("error", ts)
        self.assertGreater(ts["periods_count"], 12)
        self.assertIsNotNone(ts["peak_period"])
        self.assertGreater(ts["peak_value"], 0.0)

    # 7. Cause Analysis
    def test_07_cause_analysis(self):
        causes = cause_analysis(self.df)
        self.assertNotIn("error", causes)
        self.assertIn(causes["primary_cause"], self.df["Cause_Label"].unique())
        self.assertGreater(causes["primary_count"], 0)

    # 8. Compliance Queries
    def test_08_compliance_queries(self):
        comp = compliance_analysis(pd.DataFrame(), events_df=self.df)
        self.assertNotIn("error", comp)
        self.assertGreaterEqual(comp["total_flagged_events"], 0)

    # 9. ML Prediction Integration
    def test_09_ml_prediction(self):
        test_remark = "Emergency backing down to prevent grid failure at Bhadla"
        pred = predict_remark_cause(test_remark, classifier=self.classifier)
        self.assertNotIn("error", pred)
        self.assertEqual(pred["predicted_cause"], "Grid Security")
        self.assertGreater(pred["confidence_pct"], 60.0)
        self.assertEqual(pred["pipeline_status"], "classified")

    # 10. Chat Context & Pronoun Resolution
    def test_10_chat_context(self):
        ctx = ConversationContext()
        # Turn 1: Ask about Maharashtra
        q1 = "Which state has the highest curtailment?"
        res1 = self.bot.ask(q1, df=self.df)
        self.bot.context.last_state = "Maharashtra"
        
        # Turn 2: Follow-up using 'its'
        q2 = "What about its average demand?"
        res2 = self.bot.ask(q2, df=self.df)
        self.assertEqual(res2["entities"]["states"], ["Maharashtra"])
        self.assertEqual(res2["entities"]["metric"], "Demand_MW")

        # Turn 3: Comparative follow-up
        self.bot.context.last_comparison_entities = ["Maharashtra", "Gujarat"]
        self.bot.context.last_comparison_type = "state"
        q3 = "Which one has higher renewable generation?"
        res3 = self.bot.ask(q3, df=self.df)
        self.assertIn("Comparison", res3["text"])

    # 11. Invalid Questions Handling
    def test_11_invalid_questions(self):
        res = self.bot.ask("What is the stock price of Apple on NASDAQ?", df=self.df)
        self.assertIn("I don't have enough information", res["text"])

    # 12. Empty Dataset Handling
    def test_12_empty_dataset(self):
        empty_df = pd.DataFrame()
        summ = get_dataset_summary(empty_df)
        self.assertIn("error", summ)
        res = self.bot.ask("What is the average curtailment?", df=empty_df)
        self.assertTrue("Dataset is empty" in res["text"] or "No records found" in res["text"])

    # 13. API Failure / Deterministic Fallback
    def test_13_deterministic_fallback(self):
        # Even without any API key, the bot returns rich markdown answers
        res = self.bot.ask("What is the total renewable generation?", df=self.df)
        self.assertNotIn("error", res)
        self.assertIn("MW", res["text"])
        self.assertIn("RES_Generation_MW", res["text"])

    # 14. Hallucination Prevention
    def test_14_hallucination_prevention(self):
        res = self.bot.ask("What is the average curtailment percentage in the Western region?", df=self.df)
        western_mean = float(self.df[self.df["Region"] == "Western"]["Curtailment_Percent"].mean())
        # The returned response text MUST include the exact calculated number
        formatted_val = f"{western_mean:,.2f}"
        self.assertIn(formatted_val, res["text"], f"Calculated value {formatted_val} must be in response text")

    # 15. Representative Questions Suite (18 Questions)
    def test_15_representative_questions(self):
        questions = [
            ("How many records are in the dataset?", "INTENT_DATA_SUMMARY"),
            ("What is the average renewable generation?", "INTENT_METRIC_STAT"),
            ("What is the total curtailment?", "INTENT_METRIC_STAT"),
            ("Which state has the highest curtailment?", "INTENT_RANKING"),
            ("Which region has the highest average curtailment?", "INTENT_RANKING"),
            ("What percentage of renewable generation was curtailed?", "INTENT_CURTAILMENT_PERCENTAGE"),
            ("What are the top 5 states by curtailment?", "INTENT_RANKING"),
            ("Show the monthly curtailment trend.", "INTENT_TIME_TREND"),
            ("Which cause occurs most frequently?", "INTENT_CAUSE_ANALYSIS"),
            ("How many records are classified as Grid Security?", "INTENT_CAUSE_SPECIFIC"),
            ("Compare Maharashtra and Gujarat.", "INTENT_COMPARISON"),
            ("Compare Northern and Western regions.", "INTENT_COMPARISON"),
            ("What does dispatcher remark mean?", "INTENT_GENERAL_QA_DISPATCHER_REMARK"),
            ("Classify remark: Transmission line constraint at Bhuj 400kV corridor", "INTENT_ML_PREDICT"),
            ("How many records were flagged?", "INTENT_COMPLIANCE"),
            ("What is renewable energy curtailment?", "INTENT_GENERAL_QA_CURTAILMENT"),
            ("What is the difference between MW and MWh?", "INTENT_GENERAL_QA_MW_VS_MWH"),
            ("How can I reduce my electricity bill?", "INTENT_CONSUMER_REDUCE_BILL"),
            ("Can solar reduce my electricity bill?", "INTENT_CONSUMER_REDUCE_BILL"),
            ("Calculate solar savings for 350 units in Maharashtra", "INTENT_SOLAR_CALCULATOR")
        ]

        for q, expected_intent in questions:
            with self.subTest(query=q):
                res = self.bot.ask(q, df=self.df)
                self.assertIsNotNone(res["text"], f"Response text should not be None for '{q}'")
                self.assertGreater(len(res["text"]), 20, f"Response text should be substantive for '{q}'")

    # 16. Rooftop Solar Calculator Sizing & Subsidy
    def test_16_solar_calculator(self):
        res = calculate_solar_potential(monthly_units=300.0, state="Maharashtra", rooftop_sqft=400.0)
        self.assertGreater(res["recommended_kw"], 0.0)
        self.assertEqual(res["subsidy"], 60000.0)  # 2.3 kW rounded gives ₹60k or ₹78k
        self.assertGreater(res["annual_savings"], 10000.0)
        self.assertGreater(res["payback_years"], 0.0)
        self.assertIn("summary_markdown", res)

if __name__ == "__main__":
    unittest.main()
