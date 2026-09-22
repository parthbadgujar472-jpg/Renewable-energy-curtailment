"""
FastAPI REST API Layer (Agent 4 - Warden)
Exposes validated curtailment data, compliance scorecards, and CSV export.
"""

import os
import sys
from typing import Optional, List
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import io

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = FastAPI(
    title="RE Curtailment & Regulatory Compliance API",
    description="REST API for Indian Renewable Energy Curtailment Events, NLP Cause Classification, and Compliance Scorecard.",
    version="1.0.0"
)

CLASSIFIED_EVENTS_PATH = "data/processed/classified_curtailment_events.csv"
COMPLIANCE_PATH = "data/processed/compliance_scorecard.csv"

def get_events_df() -> pd.DataFrame:
    if not os.path.exists(CLASSIFIED_EVENTS_PATH):
        from agents.analyst.classifier import run_classifier_pipeline
        _, _, df = run_classifier_pipeline()
        return df
    return pd.read_csv(CLASSIFIED_EVENTS_PATH)

def get_compliance_df() -> pd.DataFrame:
    if not os.path.exists(COMPLIANCE_PATH):
        from agents.warden.compliance import compute_compliance_scorecard
        df_events = get_events_df()
        return compute_compliance_scorecard(df_events)
    return pd.read_csv(COMPLIANCE_PATH)

@app.get("/events")
def get_curtailment_events(
    region: Optional[str] = Query(None, description="Filter by region (e.g. 'Southern Region')"),
    state: Optional[str] = Query(None, description="Filter by state (e.g. 'Tamil Nadu')"),
    cause: Optional[str] = Query(None, description="Filter by NLP cause classification"),
    validation_status: Optional[str] = Query(None, description="Filter by validation status ('confirmed', 'mismatch')"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum NLP classification confidence score"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    from agents.analyst.classifier import get_filtered_events
    df = get_events_df()
    
    total_count, paginated_df = get_filtered_events(
        df, region=region, state=state, cause=cause, 
        validation_status=validation_status, 
        min_confidence=min_confidence, 
        limit=limit, offset=offset
    )
    
    return {
        "total_records": total_count,
        "limit": limit,
        "offset": offset,
        "events": paginated_df.to_dict(orient="records")
    }

@app.get("/compliance")
def get_compliance_scorecard(region: Optional[str] = None):
    from agents.warden.compliance import get_compliance_scorecard_filtered
    df = get_compliance_df()
    df_filtered = get_compliance_scorecard_filtered(df, region=region)
    return {
        "total_regions": len(df_filtered),
        "scorecard": df_filtered.to_dict(orient="records")
    }

@app.get("/export/csv")
def export_csv_file(region: Optional[str] = None, state: Optional[str] = None):
    from agents.analyst.classifier import get_filtered_events
    df = get_events_df()
    
    # We use get_filtered_events without limit/offset to get the full filtered dataset
    _, df_filtered = get_filtered_events(df, region=region, state=state, limit=None, offset=0)
        
    stream = io.StringIO()
    df_filtered.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=curtailment_events_export.csv"
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
