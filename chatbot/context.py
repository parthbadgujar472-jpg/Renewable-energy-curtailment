"""
Conversation Context & Multi-turn Session State Manager.
Handles pronoun resolution, anaphora tracking, and state persistence.
"""

from typing import Dict, Any, List, Optional, Tuple
import copy
import re

class ConversationContext:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.last_state: Optional[str] = None
        self.last_region: Optional[str] = None
        self.last_metric: Optional[str] = "Curtailment_MW"
        self.last_cause: Optional[str] = None
        self.last_comparison_entities: List[str] = []
        self.last_comparison_type: Optional[str] = None  # 'state' or 'region'
        self.last_temporal_filter: Dict[str, Any] = {}
        self.last_intent: Optional[str] = None
        self.last_payload: Optional[Dict[str, Any]] = None

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Appends a turn to conversation history."""
        entry = {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.history.append(entry)

    def update_from_entities(
        self,
        entities: Dict[str, Any],
        intent: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> None:
        """Updates internal memory from newly extracted entities and intent."""
        self.last_intent = intent
        if payload:
            self.last_payload = payload

        if entities.get("states"):
            if len(entities["states"]) == 1:
                self.last_state = entities["states"][0]
            elif len(entities["states"]) >= 2:
                self.last_comparison_entities = entities["states"][:2]
                self.last_comparison_type = "state"
                self.last_state = entities["states"][0]

        if entities.get("regions"):
            if len(entities["regions"]) == 1:
                self.last_region = entities["regions"][0]
            elif len(entities["regions"]) >= 2:
                self.last_comparison_entities = entities["regions"][:2]
                self.last_comparison_type = "region"
                self.last_region = entities["regions"][0]

        if entities.get("metric"):
            self.last_metric = entities["metric"]

        if entities.get("cause"):
            self.last_cause = entities["cause"]

        temp_filter = {}
        for k in ["year", "month", "quarter", "season"]:
            if entities.get(k):
                temp_filter[k] = entities[k]
        if temp_filter:
            self.last_temporal_filter = temp_filter

    def resolve_references(self, query: str, entities: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Resolves pronouns ('its', 'it', 'that state', 'which one', 'the other one')
        and elliptical follow-ups ('What about Gujarat?', 'And demand?').
        """
        resolved_q = query
        resolved_entities = copy.deepcopy(entities)
        q_lower = query.lower().strip()

        # 1. Pronoun 'its' or 'their' (e.g. 'What about its average demand?')
        if re.search(r"\b(its|it's|their|that state's|that state|this state)\b", q_lower):
            if self.last_state and not resolved_entities["states"]:
                resolved_entities["states"] = [self.last_state]
                resolved_q = re.sub(r"\b(its|it's|their|that state's|that state|this state)\b", self.last_state, resolved_q, flags=re.IGNORECASE)
            elif self.last_region and not resolved_entities["regions"]:
                resolved_entities["regions"] = [self.last_region]
                resolved_q = re.sub(r"\b(its|it's|their|that region's|that region|this region)\b", self.last_region, resolved_q, flags=re.IGNORECASE)

        # 2. Comparative follow-up: 'Which one has higher ...?' or 'Which has higher ...?'
        if (
            re.search(r"\b(which one|which of them|who|which)\b", q_lower)
            and re.search(r"\b(higher|more|lower|less|greater)\b", q_lower)
            and len(resolved_entities["states"]) < 2
            and len(resolved_entities["regions"]) < 2
        ):
            if len(self.last_comparison_entities) >= 2:
                if self.last_comparison_type == "state":
                    resolved_entities["states"] = self.last_comparison_entities[:2]
                elif self.last_comparison_type == "region":
                    resolved_entities["regions"] = self.last_comparison_entities[:2]

        # 3. Elliptical replacement: 'What about Gujarat?' / 'And in Maharashtra?'
        if (
            re.search(r"^(what about|and in|how about|and for|check)\s+([a-zA-Z\s&]+)\??$", q_lower)
            and len(resolved_entities["states"]) == 1
            and not resolved_entities["metric"]
        ):
            # Carry over the last metric
            if self.last_metric:
                resolved_entities["metric"] = self.last_metric

        # 4. Elliptical metric follow-up: 'What about average demand?' / 'And renewable generation?'
        if (
            not resolved_entities["states"]
            and not resolved_entities["regions"]
            and resolved_entities["metric"]
            and self.last_state
        ):
            # If the user previously asked about a state and now asks about another metric without specifying state:
            if re.search(r"^(what about|and|how about|what is|tell me)\s+", q_lower):
                resolved_entities["states"] = [self.last_state]

        # 5. Visual follow-up: 'Show that on a chart' / 'Plot this'
        if re.search(r"\b(plot this|show that as a chart|visualize this|make a chart)\b", q_lower):
            if self.last_metric and not resolved_entities["metric"]:
                resolved_entities["metric"] = self.last_metric
            if self.last_state and not resolved_entities["states"]:
                resolved_entities["states"] = [self.last_state]

        return resolved_q, resolved_entities

    def clear(self) -> None:
        """Clears all session context."""
        self.history = []
        self.last_state = None
        self.last_region = None
        self.last_metric = "Curtailment_MW"
        self.last_cause = None
        self.last_comparison_entities = []
        self.last_comparison_type = None
        self.last_temporal_filter = {}
        self.last_intent = None
        self.last_payload = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes context for state persistence."""
        return {
            "history": self.history,
            "last_state": self.last_state,
            "last_region": self.last_region,
            "last_metric": self.last_metric,
            "last_cause": self.last_cause,
            "last_comparison_entities": self.last_comparison_entities,
            "last_comparison_type": self.last_comparison_type,
            "last_temporal_filter": self.last_temporal_filter,
            "last_intent": self.last_intent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """Reconstructs context object from dictionary."""
        ctx = cls()
        ctx.history = data.get("history", [])
        ctx.last_state = data.get("last_state")
        ctx.last_region = data.get("last_region")
        ctx.last_metric = data.get("last_metric", "Curtailment_MW")
        ctx.last_cause = data.get("last_cause")
        ctx.last_comparison_entities = data.get("last_comparison_entities", [])
        ctx.last_comparison_type = data.get("last_comparison_type")
        ctx.last_temporal_filter = data.get("last_temporal_filter", {})
        ctx.last_intent = data.get("last_intent")
        return ctx
