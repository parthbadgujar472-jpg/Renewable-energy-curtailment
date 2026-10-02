"""
Natural Language Query Parser & Intent Classifier for Energy Intelligence Assistant.
Robust rule-based, regex-driven, and entity-extracting parser that requires no external API.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# All 36 Indian States and Union Territories with common aliases
STATE_CANONICAL_MAP = {
    "andhra pradesh": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chandigarh": "Chandigarh",
    "chhattisgarh": "Chhattisgarh",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi",
    "nct of delhi": "Delhi",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "gj": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "hp": "Himachal Pradesh",
    "jammu & kashmir": "Jammu & Kashmir",
    "jammu and kashmir": "Jammu & Kashmir",
    "j&k": "Jammu & Kashmir",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "ka": "Karnataka",
    "kerala": "Kerala",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "mh": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "rj": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    "andaman & nicobar": "Andaman & Nicobar",
    "andaman and nicobar": "Andaman & Nicobar"
}

# Regional mappings
REGION_CANONICAL_MAP = {
    "northern": "Northern",
    "nr": "Northern",
    "north": "Northern",
    "western": "Western",
    "wr": "Western",
    "west": "Western",
    "southern": "Southern",
    "sr": "Southern",
    "south": "Southern",
    "eastern": "Eastern",
    "er": "Eastern",
    "east": "Eastern",
    "ner": "NER",
    "north eastern": "NER",
    "north-eastern": "NER",
    "northeast": "NER"
}

# Metric keywords to canonical column names
METRIC_SYNONYMS = {
    "Curtailment_MW": [
        "curtailment", "curtailed", "wasted", "curtailed energy", "curtailed_mw", 
        "curtailment_mw", "backed down", "backing down", "re curtailment"
    ],
    "Curtailment_Percent": [
        "curtailment percent", "curtailment percentage", "curtailment rate", 
        "curtailment_percent", "percent curtailed", "percentage curtailed", "% curtailed"
    ],
    "RES_Generation_MW": [
        "renewable generation", "re generation", "res generation", "generation", 
        "res_generation_mw", "green generation", "clean energy generated", "solar and wind"
    ],
    "Demand_MW": [
        "demand", "electricity demand", "power demand", "load", "demand_mw", 
        "consumption", "system demand"
    ],
    "SolarGen_MW": [
        "solar generation", "solar gen", "solar power", "solargen_mw", "solar"
    ],
    "WindGen_MW": [
        "wind generation", "wind gen", "wind power", "windgen_mw", "wind"
    ],
    "HydroGen_MW": [
        "hydro generation", "hydro gen", "hydropower", "hydrogen_mw", "hydro"
    ]
}

# Standard Cause Label matching
CAUSE_SYNONYMS = {
    "Transmission Constraint": [
        "transmission constraint", "transmission congestion", "line congestion", 
        "line loading", "thermal constraint", "corridor bottleneck", "transmission", "congestion"
    ],
    "Grid Security": [
        "grid security", "grid instability", "voltage instability", "system security", 
        "frequency instability", "stability", "instability"
    ],
    "High Frequency": [
        "high frequency", "over frequency", "over-frequency", "over generation", 
        "over-generation", "surplus generation"
    ],
    "Commercial / Discom Request": [
        "commercial", "discom request", "low demand", "economic dispatch", 
        "commercial backing down", "power surrender", "discom"
    ],
    "Maintenance / Outage": [
        "maintenance", "outage", "shutdown", "line clearance"
    ]
}

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

def extract_entities(query: str) -> Dict[str, Any]:
    """Extracts states, regions, metrics, causes, temporal filters, and numbers."""
    q_lower = query.lower()
    
    # 1. Extract States (check longer state names first to avoid substrings)
    found_states = []
    # Sort keys by length descending
    for alias in sorted(STATE_CANONICAL_MAP.keys(), key=lambda x: len(x), reverse=True):
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, q_lower):
            canonical = STATE_CANONICAL_MAP[alias]
            if canonical not in found_states:
                found_states.append(canonical)
                
    # 2. Extract Regions
    found_regions = []
    for alias in sorted(REGION_CANONICAL_MAP.keys(), key=lambda x: len(x), reverse=True):
        pattern = r"\b" + re.escape(alias) + r"(?:\s+region)?\b"
        if re.search(pattern, q_lower):
            canonical = REGION_CANONICAL_MAP[alias]
            if canonical not in found_regions:
                found_regions.append(canonical)
                
    # 3. Extract Metric
    found_metric = None
    for canonical_m, syns in METRIC_SYNONYMS.items():
        for syn in sorted(syns, key=lambda x: len(x), reverse=True):
            if re.search(r"\b" + re.escape(syn) + r"\b", q_lower):
                found_metric = canonical_m
                break
        if found_metric:
            break
            
    # Default to Curtailment_MW if curtailment is broadly referenced
    if not found_metric and ("curtail" in q_lower or "waste" in q_lower):
        found_metric = "Curtailment_MW"
        
    # 4. Extract Cause
    found_cause = None
    for canonical_cause, syns in CAUSE_SYNONYMS.items():
        for syn in sorted(syns, key=lambda x: len(x), reverse=True):
            if re.search(r"\b" + re.escape(syn) + r"\b", q_lower):
                found_cause = canonical_cause
                break
        if found_cause:
            break
            
    # 5. Extract Date / Temporal Filters
    year_match = re.search(r"\b(202[0-9])\b", q_lower)
    found_year = int(year_match.group(1)) if year_match else None
    
    found_month = None
    for m_name, m_num in MONTH_MAP.items():
        if re.search(r"\b" + re.escape(m_name) + r"\b", q_lower):
            found_month = m_num
            break
            
    found_quarter = None
    q_match = re.search(r"\bq([1-4])\b", q_lower)
    if q_match:
        found_quarter = int(q_match.group(1))
        
    found_season = None
    if re.search(r"\b(summer|pre-monsoon)\b", q_lower):
        found_season = "summer"
    elif re.search(r"\b(monsoon)\b", q_lower):
        found_season = "monsoon"
    elif re.search(r"\b(winter)\b", q_lower):
        found_season = "winter"
    elif re.search(r"\b(post-monsoon|autumn)\b", q_lower):
        found_season = "post-monsoon"
        
    # 6. Extract Aggregation Type
    stat_type = "sum"
    if re.search(r"\b(average|avg|mean)\b", q_lower):
        stat_type = "mean"
    elif re.search(r"\b(maximum|max|highest|peak|most)\b", q_lower):
        stat_type = "max"
    elif re.search(r"\b(minimum|min|lowest|least)\b", q_lower):
        stat_type = "min"
    elif re.search(r"\b(median)\b", q_lower):
        stat_type = "median"
    elif re.search(r"\b(total|sum)\b", q_lower):
        stat_type = "sum"
    elif re.search(r"\b(count|how many|number of)\b", q_lower):
        stat_type = "count"
    elif re.search(r"\b(std|standard deviation)\b", q_lower):
        stat_type = "std"
        
    # 7. Extract Top N count
    top_n = 5
    top_n_match = re.search(r"\btop\s*(\d+)\b", q_lower)
    if top_n_match:
        top_n = int(top_n_match.group(1))
    elif re.search(r"\b(highest|top|most)\b", q_lower) and not re.search(r"\btop\s*\d+\b", q_lower):
        top_n = 1
        
    # 8. Extract Solar Calculator Parameters
    units_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:units?|kwh)", q_lower)
    solar_units = float(units_match.group(1)) if units_match else None
    
    sqft_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\s*ft|sqft|square\s*feet|sq\.?\s*ft)", q_lower)
    solar_sqft = float(sqft_match.group(1)) if sqft_match else None
    
    return {
        "states": found_states,
        "regions": found_regions,
        "metric": found_metric,
        "cause": found_cause,
        "year": found_year,
        "month": found_month,
        "quarter": found_quarter,
        "season": found_season,
        "stat_type": stat_type,
        "top_n": top_n,
        "solar_units": solar_units,
        "solar_sqft": solar_sqft
    }

def classify_intent(query: str, entities: Dict[str, Any]) -> str:
    """Classifies user natural-language query into an operational intent."""
    q_lower = query.lower().strip()
    
    # ML Prediction / Cause classification query
    if (
        ("classify" in q_lower or "predict" in q_lower or "what would the model" in q_lower or "analyze this remark" in q_lower)
        and ("remark" in q_lower or "instruction" in q_lower or ":" in q_lower)
    ):
        return "INTENT_ML_PREDICT"
        
    # General Domain Definitions
    if (
        re.search(r"\bwhat is\b|\bwhat does\b|\bdefine\b|\bmeaning of\b|\bdifference between\b", q_lower)
        and not re.search(r"\b(average|total|sum|highest|lowest|max|min|curtailment in|demand in)\b", q_lower)
    ):
        if "curtailment" in q_lower:
            return "INTENT_GENERAL_QA_CURTAILMENT"
        elif "grid instability" in q_lower or "grid security" in q_lower:
            return "INTENT_GENERAL_QA_GRID_INSTABILITY"
        elif "transmission" in q_lower or "congestion" in q_lower:
            return "INTENT_GENERAL_QA_TRANSMISSION"
        elif "over-generation" in q_lower or "over generation" in q_lower or "high frequency" in q_lower:
            return "INTENT_GENERAL_QA_OVER_GENERATION"
        elif "rooftop solar" in q_lower or "solar panel" in q_lower:
            return "INTENT_GENERAL_QA_ROOFTOP_SOLAR"
        elif "mw and mwh" in q_lower or "mw vs mwh" in q_lower or "megawatt" in q_lower:
            return "INTENT_GENERAL_QA_MW_VS_MWH"
        elif "mw" in q_lower:
            return "INTENT_GENERAL_QA_MW"
        elif "dispatcher remark" in q_lower:
            return "INTENT_GENERAL_QA_DISPATCHER_REMARK"
        elif "renewable energy" in q_lower:
            return "INTENT_GENERAL_QA_RENEWABLE_ENERGY"
            
    # Consumer Energy Assistant / Rooftop Solar
    if (
        "reduce" in q_lower and ("bill" in q_lower or "electricity" in q_lower or "consumption" in q_lower)
        or "save money" in q_lower
        or "lower my bill" in q_lower
    ):
        return "INTENT_CONSUMER_REDUCE_BILL"
        
    if (
        "solar" in q_lower
        and ("useful" in q_lower or "household" in q_lower or "benefit" in q_lower or "rooftop" in q_lower)
        and entities.get("solar_units") is None
    ):
        return "INTENT_CONSUMER_SOLAR_BENEFITS"
        
    if "solar generation affect" in q_lower or "duck curve" in q_lower:
        return "INTENT_CONSUMER_GRID_IMPACT"
        
    if ("when is" in q_lower or "what time" in q_lower) and ("renewable" in q_lower or "generation" in q_lower or "peak" in q_lower):
        return "INTENT_CONSUMER_PEAK_RE"
        
    if entities.get("solar_units") is not None or "calculate solar" in q_lower or "solar estimate" in q_lower:
        return "INTENT_SOLAR_CALCULATOR"
        
    # Compliance Questions
    if (
        "flagged" in q_lower
        or "compliance" in q_lower
        or "non-compliant" in q_lower
        or "scorecard" in q_lower
        or "audit" in q_lower
        or "rule" in q_lower
    ):
        return "INTENT_COMPLIANCE"
        
    # Dispatcher Remark Search
    if (
        ("find remark" in q_lower or "show remark" in q_lower or "search remark" in q_lower or "mentioning" in q_lower)
        and ("remark" in q_lower or "remarks" in q_lower or "overloading" in q_lower or "voltage" in q_lower)
    ):
        return "INTENT_REMARK_SEARCH"
        
    # Correlation Analysis
    if "correlation" in q_lower or "relationship between" in q_lower:
        return "INTENT_CORRELATION"
        
    # Cause Analysis
    if (
        "most common reason" in q_lower
        or "main cause" in q_lower
        or "most frequent cause" in q_lower
        or "cause occurs most" in q_lower
        or "distribution of cause" in q_lower
        or "cause distribution" in q_lower
        or "breakdown of cause" in q_lower
        or "why was renewable energy curtailed" in q_lower
    ):
        return "INTENT_CAUSE_ANALYSIS"
        
    if entities.get("cause") and ("how many" in q_lower or "count" in q_lower or "percentage" in q_lower):
        return "INTENT_CAUSE_SPECIFIC"
        
    # Comparisons: State vs State or Region vs Region
    if (
        "compare" in q_lower
        or (len(entities["states"]) >= 2)
        or (len(entities["regions"]) >= 2)
        or ("higher" in q_lower and ("or" in q_lower or "than" in q_lower))
        or ("which has higher" in q_lower)
        or ("difference between" in q_lower)
    ):
        if len(entities["states"]) >= 2 or len(entities["regions"]) >= 2 or "compare" in q_lower:
            return "INTENT_COMPARISON"
            
    # Time Series / Trend Analysis
    if (
        "trend" in q_lower
        or "change over time" in q_lower
        or "monthly curtailment" in q_lower
        or "over time" in q_lower
        or "by month" in q_lower
        or "which month" in q_lower
        or "by year" in q_lower
    ):
        return "INTENT_TIME_TREND"
        
    # Ranking: Top N, Highest, Lowest State or Region
    if (
        "which state" in q_lower
        or "which region" in q_lower
        or "top" in q_lower
        or "highest" in q_lower
        or "lowest" in q_lower
        or "rank" in q_lower
        or "maximum curtailment" in q_lower
        or "curtailed the most" in q_lower
    ):
        return "INTENT_RANKING"
        
    # Ratio / Curtailment Percentage
    if (
        "percentage of" in q_lower and "curtail" in q_lower
        or "curtailment percentage" in q_lower
        or "curtailment rate" in q_lower
        or "how much re was curtailed" in q_lower
    ):
        return "INTENT_CURTAILMENT_PERCENTAGE"
        
    # Metric Statistics: Average, Sum, Max, Min, Count
    if (
        "average" in q_lower
        or "total" in q_lower
        or "sum" in q_lower
        or "how many" in q_lower
        or "how much" in q_lower
        or "mean" in q_lower
        or "median" in q_lower
        or "minimum" in q_lower
        or "maximum" in q_lower
        or "records" in q_lower
        or entities.get("metric")
    ):
        return "INTENT_METRIC_STAT"
        
    # Visual Chart Request
    if re.search(r"\b(plot|chart|graph|show a plot|visualize)\b", q_lower):
        return "INTENT_CHART"
        
    # Dataset Summary / Overview
    if re.search(r"\b(overview|summary|summarize|dataset|info|about)\b", q_lower):
        return "INTENT_DATA_SUMMARY"
        
    return "INTENT_UNKNOWN"
