"""
RE Curtailment Analytics & Regulatory Compliance - AI Energy Intelligence Assistant
Modular Chatbot Package
"""

from chatbot.chatbot import EnergyChatbot
from chatbot.data_agent import DataAgent
from chatbot.context import ConversationContext
from chatbot.analytics import (
    get_dataset_summary,
    get_column_stat,
    get_top_n,
    compare_entities,
    compare_metrics,
    time_series_analysis,
    cause_analysis,
    correlation_analysis,
    search_remarks,
    predict_remark_cause,
    compliance_analysis,
)

__all__ = [
    "EnergyChatbot",
    "DataAgent",
    "ConversationContext",
    "get_dataset_summary",
    "get_column_stat",
    "get_top_n",
    "compare_entities",
    "compare_metrics",
    "time_series_analysis",
    "cause_analysis",
    "correlation_analysis",
    "search_remarks",
    "predict_remark_cause",
    "compliance_analysis",
]
