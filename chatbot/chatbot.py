"""
High-Level EnergyChatbot Facade.
Provides unified entry point for Streamlit dashboard and API integrations.
"""

from typing import Dict, Any, Optional
import pandas as pd
from chatbot.data_agent import DataAgent
from chatbot.context import ConversationContext

class EnergyChatbot:
    def __init__(self, classifier=None):
        self.agent = DataAgent(classifier=classifier)
        self.context = ConversationContext()

    def ask(
        self,
        query: str,
        df: pd.DataFrame,
        compliance_df: Optional[pd.DataFrame] = None,
        active_filters: Optional[Dict[str, Any]] = None,
        sync_filters: bool = True
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end analytical query.
        Returns:
            {
                "text": str,
                "chart": Optional[go.Figure],
                "table": Optional[pd.DataFrame],
                "calculation": Optional[str],
                "scope": str,
                "intent": str
            }
        """
        return self.agent.process_query(
            query=query,
            df=df,
            compliance_df=compliance_df,
            context=self.context,
            active_filters=active_filters,
            sync_filters=sync_filters
        )

    def clear_history(self) -> None:
        """Resets the conversation context."""
        self.context.clear()

    @property
    def provider_name(self) -> str:
        """Returns the active LLM or NLG engine name."""
        return self.agent.llm_provider.provider_name
