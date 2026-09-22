"""
Synthetic Data Generator for RE Curtailment Events (Agent 3 - Analyst)
Generates realistic sample records with synthetic flag for model training & dashboard demo.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Taxonomies and realistic phrase templates for dispatcher remarks
REMARK_TEMPLATES = {
    "Grid Security": [
        "Grid security alert: voltage instability detected at {substation}",
        "Emergency backing down to prevent grid failure at {substation}",
        "System security constraint enforced by {rldc} dispatcher",
        "Over-generation mitigation required for grid stability",
        "Reactive power compensation constraint at {substation} grid"
    ],
    "High Frequency": [
        "High frequency in grid ({freq} Hz), backing down instructed by {rldc}",
        "Frequency higher than statutory limit ({freq} Hz), RE reduction mandated",
        "Over-frequency condition ({freq} Hz) detected across regional grid",
        "Frequency control directive: reduce generation immediately",
        "System frequency surge ({freq} Hz), active power curtailment executed"
    ],
    "Transmission Constraint": [
        "Transmission line constraint at {substation} 400kV corridor",
        "Transmission congestion on {substation} to {substation_2} 765kV line",
        "Line loading exceeded thermal capacity limit at {substation}",
        "N-1 contingency constraint triggered on evacuation line",
        "Inter-regional corridor bottleneck, backing down required"
    ],
    "Commercial / Discom Request": [
        "DISCOM commercial request due to low demand period",
        "Commercial backing down order from state DISCOM ({discom})",
        "Low demand period discom backing down request",
        "Economic dispatch instruction from SLDC control room",
        "Power surrender by buying utility due to off-peak tariff"
    ],
    "Maintenance / Outage": [
        "Substation maintenance work scheduled at {substation}",
        "Bay maintenance shutdown at {substation} RE pooling station",
        "Transformer maintenance outage at evacuation yard",
        "Planned line clearance for grid upgrade work",
        "Protection relay testing shutdown at pooling station"
    ]
}

SUBSTATIONS = ["Kayathar", "Bhuj", "Bhadla", "Pavagada", "Kurnool", "Rewa", "Tuticorin", "Khavda", "Muppandal"]
RLDCS = ["SRLDC", "WRLDC", "NRLDC", "ERLDC"]
DISCOMS = ["Bescom", "Tangedco", "Gurowvnl", "Discom-West", "Javvnl"]

PLANTS = [
    {"id": "TN_SOLAR_01", "region": "Southern Region", "state": "Tamil Nadu", "type": "Solar", "cap": 500},
    {"id": "TN_WIND_02", "region": "Southern Region", "state": "Tamil Nadu", "type": "Wind", "cap": 350},
    {"id": "KA_SOLAR_01", "region": "Southern Region", "state": "Karnataka", "type": "Solar", "cap": 600},
    {"id": "RJ_SOLAR_01", "region": "Western Region", "state": "Rajasthan", "type": "Solar", "cap": 1000},
    {"id": "GJ_WIND_01", "region": "Western Region", "state": "Gujarat", "type": "Wind", "cap": 400},
    {"id": "AP_SOLAR_02", "region": "Southern Region", "state": "Andhra Pradesh", "type": "Solar", "cap": 450},
    {"id": "MP_SOLAR_01", "region": "Western Region", "state": "Madhya Pradesh", "type": "Solar", "cap": 500},
]

def generate_synthetic_data(num_records=750, output_path="data/processed/synthetic_curtailment_events.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_date = datetime(2026, 6, 1)
    records = []
    
    for i in range(num_records):
        plant = random.choice(PLANTS)
        date = start_date + timedelta(days=random.randint(0, 80))
        hour = random.randint(6, 18) if plant["type"] == "Solar" else random.randint(0, 23)
        time_str = f"{date.strftime('%Y-%m-%d')} {hour:02d}:00:00"
        
        # Determine cause taxonomy
        cause = random.choice(list(REMARK_TEMPLATES.keys()))
        
        # Build dispatcher remark
        template = random.choice(REMARK_TEMPLATES[cause])
        freq = round(random.uniform(50.05, 50.15), 2)
        sub1 = random.choice(SUBSTATIONS)
        sub2 = random.choice([s for s in SUBSTATIONS if s != sub1])
        rldc = random.choice(RLDCS)
        discom = random.choice(DISCOMS)
        
        remark = template.format(
            substation=sub1,
            substation_2=sub2,
            freq=freq,
            rldc=rldc,
            discom=discom
        )
        
        scheduled_mw = round(random.uniform(plant["cap"] * 0.4, plant["cap"] * 0.95), 1)
        curtailed_mw = round(random.uniform(15.0, scheduled_mw * 0.4), 1)
        actual_mw = round(scheduled_mw - curtailed_mw, 1)
        
        # Synthetic deviation calculation (ΔG = Scheduled - Actual)
        # Occasionally introduce a slight discrepancy for cross-validation demo
        if random.random() < 0.15:
            deviation_mw = round(curtailed_mw * random.uniform(0.6, 1.4), 1) # mismatch
        else:
            deviation_mw = curtailed_mw # confirmed match
            
        records.append({
            "event_id": f"EVT-2026-{i+1001:04d}",
            "timestamp": time_str,
            "region": plant["region"],
            "state": plant["state"],
            "plant_id": plant["id"],
            "generation_type": plant["type"],
            "plant_capacity_mw": plant["cap"],
            "scheduled_mw": scheduled_mw,
            "actual_mw": actual_mw,
            "curtailed_mw": curtailed_mw,
            "deviation_mw": deviation_mw,
            "dispatcher_remark": remark,
            "true_cause_label": cause,
            "is_synthetic": True,
            "source_document_id": f"DOC-{date.strftime('%Y%m%d')}-{plant['state'][:2].upper()}"
        })
        
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"[Analyst Agent] Successfully generated {len(df)} synthetic records to '{output_path}'.")
    return df

if __name__ == "__main__":
    generate_synthetic_data()
