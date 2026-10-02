"""
Controlled Analytics Engine for RE Curtailment & Regulatory Compliance.
Executes deterministic pandas computations without eval() or exec().
Source of truth for all numerical and statistical queries.
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Canonical numerical columns in the dataset
NUMERIC_COLUMNS = {
    "Curtailment_MW",
    "RES_Generation_MW",
    "Demand_MW",
    "Curtailment_Percent",
    "MaximumDemand_MW",
    "HydroGen_MW",
    "WindGen_MW",
    "SolarGen_MW",
    "OtherRE_MW",
    "TotalGeneration_MW",
    "RE_Available_MW",
    "EnergyShortage_MU"
}

def sanitize_dataframe_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Safely converts the Date column to datetime to handle mixed types."""
    if df.empty or "Date" not in df.columns:
        return df
    
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df = df.copy()
        df["Date_dt"] = pd.to_datetime(df["Date"], errors="coerce")
    else:
        df = df.copy()
        df["Date_dt"] = df["Date"]
        
    return df

def apply_filters(
    df: pd.DataFrame,
    region: Optional[str] = None,
    state: Optional[str] = None,
    cause: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    quarter: Optional[int] = None,
    season: Optional[str] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """Applies controlled categorical and temporal filters to dataframe."""
    if df.empty:
        return df, ["Dataset is empty"]
        
    df_filtered = df.copy()
    filter_descriptions = []
    
    # Categorical filters
    if region and "Region" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Region"].str.strip().str.lower() == region.strip().lower()]
        filter_descriptions.append(f"Region = {region}")
        
    if state and "State" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["State"].str.strip().str.lower() == state.strip().lower()]
        filter_descriptions.append(f"State = {state}")
        
    if cause and "Cause_Label" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Cause_Label"].str.strip().str.lower() == cause.strip().lower()]
        filter_descriptions.append(f"Cause = {cause}")
        
    # Date filters
    df_filtered = sanitize_dataframe_dates(df_filtered)
    
    if "Date_dt" in df_filtered.columns and df_filtered["Date_dt"].notna().any():
        if year:
            df_filtered = df_filtered[df_filtered["Date_dt"].dt.year == year]
            filter_descriptions.append(f"Year = {year}")
            
        if month:
            df_filtered = df_filtered[df_filtered["Date_dt"].dt.month == month]
            filter_descriptions.append(f"Month = {month}")
            
        if quarter:
            df_filtered = df_filtered[df_filtered["Date_dt"].dt.quarter == quarter]
            filter_descriptions.append(f"Quarter = Q{quarter}")
            
        if season:
            season_clean = season.strip().lower()
            if season_clean in ["summer", "pre-monsoon"]:
                # Summer in India: March, April, May (months 3, 4, 5)
                df_filtered = df_filtered[df_filtered["Date_dt"].dt.month.isin([3, 4, 5])]
                filter_descriptions.append("Season = Summer (Mar-May)")
            elif season_clean in ["monsoon", "southwest monsoon"]:
                # Monsoon in India: June, July, August, September (months 6, 7, 8, 9)
                df_filtered = df_filtered[df_filtered["Date_dt"].dt.month.isin([6, 7, 8, 9])]
                filter_descriptions.append("Season = Monsoon (Jun-Sep)")
            elif season_clean in ["winter"]:
                # Winter in India: December, January, February (months 12, 1, 2)
                df_filtered = df_filtered[df_filtered["Date_dt"].dt.month.isin([12, 1, 2])]
                filter_descriptions.append("Season = Winter (Dec-Feb)")
            elif season_clean in ["post-monsoon", "autumn"]:
                # Post-monsoon: October, November (months 10, 11)
                df_filtered = df_filtered[df_filtered["Date_dt"].dt.month.isin([10, 11])]
                filter_descriptions.append("Season = Post-Monsoon (Oct-Nov)")
                
        if start_date:
            try:
                s_dt = pd.to_datetime(start_date)
                df_filtered = df_filtered[df_filtered["Date_dt"] >= s_dt]
                filter_descriptions.append(f"From {start_date}")
            except Exception:
                pass
                
        if end_date:
            try:
                e_dt = pd.to_datetime(end_date)
                df_filtered = df_filtered[df_filtered["Date_dt"] <= e_dt]
                filter_descriptions.append(f"To {end_date}")
            except Exception:
                pass
                
    scope_str = ", ".join(filter_descriptions) if filter_descriptions else "Full Dataset"
    return df_filtered, [scope_str]

def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates an executive statistical summary of the loaded dataset."""
    if df.empty:
        return {"error": "Dataset is empty or not loaded."}
        
    df_safe = sanitize_dataframe_dates(df)
    
    total_records = len(df)
    date_min = df_safe["Date_dt"].min() if "Date_dt" in df_safe.columns and df_safe["Date_dt"].notna().any() else None
    date_max = df_safe["Date_dt"].max() if "Date_dt" in df_safe.columns and df_safe["Date_dt"].notna().any() else None
    
    date_range_str = f"{date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')}" if pd.notna(date_min) and pd.notna(date_max) else "N/A"
    
    total_curtailment_mw = float(df["Curtailment_MW"].sum()) if "Curtailment_MW" in df.columns else 0.0
    avg_curtailment_mw = float(df["Curtailment_MW"].mean()) if "Curtailment_MW" in df.columns else 0.0
    max_curtailment_mw = float(df["Curtailment_MW"].max()) if "Curtailment_MW" in df.columns else 0.0
    
    total_re_gen_mw = float(df["RES_Generation_MW"].sum()) if "RES_Generation_MW" in df.columns else 0.0
    avg_re_gen_mw = float(df["RES_Generation_MW"].mean()) if "RES_Generation_MW" in df.columns else 0.0
    
    total_demand_mw = float(df["Demand_MW"].sum()) if "Demand_MW" in df.columns else 0.0
    avg_demand_mw = float(df["Demand_MW"].mean()) if "Demand_MW" in df.columns else 0.0
    
    avg_curtailment_pct = float(df["Curtailment_Percent"].mean()) if "Curtailment_Percent" in df.columns else (
        (total_curtailment_mw / (total_re_gen_mw + total_curtailment_mw) * 100) if (total_re_gen_mw + total_curtailment_mw) > 0 else 0.0
    )
    
    regions = df["Region"].dropna().unique().tolist() if "Region" in df.columns else []
    states = df["State"].dropna().unique().tolist() if "State" in df.columns else []
    causes = df["Cause_Label"].dropna().unique().tolist() if "Cause_Label" in df.columns else []
    
    calc_explanation = (
        f"Aggregated {total_records:,} rows across {len(states)} states and {len(regions)} regions.\n"
        f"Sum(Curtailment_MW) = {total_curtailment_mw:,.1f} MW\n"
        f"Sum(RES_Generation_MW) = {total_re_gen_mw:,.1f} MW\n"
        f"Sum(Demand_MW) = {total_demand_mw:,.1f} MW\n"
        f"Mean(Curtailment_Percent) = {avg_curtailment_pct:.2f}%"
    )
    
    return {
        "total_records": total_records,
        "date_range": date_range_str,
        "total_curtailment_mw": total_curtailment_mw,
        "avg_curtailment_mw": avg_curtailment_mw,
        "max_curtailment_mw": max_curtailment_mw,
        "total_re_gen_mw": total_re_gen_mw,
        "avg_re_gen_mw": avg_re_gen_mw,
        "total_demand_mw": total_demand_mw,
        "avg_demand_mw": avg_demand_mw,
        "avg_curtailment_pct": avg_curtailment_pct,
        "regions_count": len(regions),
        "states_count": len(states),
        "causes_count": len(causes),
        "regions_list": regions,
        "states_list": states,
        "causes_list": causes,
        "calculation": calc_explanation
    }

def get_column_stat(
    df: pd.DataFrame,
    column: str,
    stat_type: str = "mean",
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes controlled statistic (mean, sum, median, min, max, std, count) for a column.
    """
    if df.empty:
        return {"error": "Dataset is empty."}
        
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {
            "error": f"No records found matching the specified filter criteria ({scope}).",
            "scope": scope,
            "count": 0
        }
        
    if column not in filtered_df.columns:
        return {
            "error": f"Column '{column}' was not found in the current dataset. Available columns: {list(filtered_df.columns)[:8]}...",
            "scope": scope
        }
        
    series = pd.to_numeric(filtered_df[column], errors="coerce").dropna()
    if series.empty:
        return {
            "error": f"Column '{column}' contains no numeric values in the selected scope ({scope}).",
            "scope": scope
        }
        
    stat_lower = stat_type.lower()
    val = 0.0
    formula_desc = ""
    
    if stat_lower in ["mean", "avg", "average"]:
        val = float(series.mean())
        formula_desc = f"Sum({column}) / Count({column}) = {series.sum():,.2f} / {len(series):,}"
    elif stat_lower in ["sum", "total"]:
        val = float(series.sum())
        formula_desc = f"Sum of {len(series):,} values in {column}"
    elif stat_lower in ["median"]:
        val = float(series.median())
        formula_desc = f"50th percentile of {len(series):,} values in {column}"
    elif stat_lower in ["min", "minimum", "lowest"]:
        val = float(series.min())
        formula_desc = f"Minimum value in {column}"
    elif stat_lower in ["max", "maximum", "highest", "peak"]:
        val = float(series.max())
        formula_desc = f"Maximum value in {column}"
    elif stat_lower in ["std", "standard deviation", "std_dev"]:
        val = float(series.std())
        formula_desc = f"Standard deviation of {column} (N={len(series):,})"
    elif stat_lower in ["count"]:
        val = float(len(series))
        formula_desc = f"Total count of non-null records in {column}"
    else:
        return {"error": f"Unsupported statistic type '{stat_type}'. Supported: mean, sum, median, min, max, std, count."}
        
    calc_str = f"df['{column}'].{stat_lower}() on {scope} -> Result: {val:,.2f}\nCalculation: {formula_desc}"
    
    return {
        "column": column,
        "stat_type": stat_lower,
        "value": val,
        "count": len(series),
        "scope": scope,
        "calculation": calc_str
    }

def get_curtailment_percentage_analysis(
    df: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes both the average Curtailment_Percent and the macro-level curtailment ratio.
    Ratio = (Total Curtailment_MW) / (Total RES_Generation_MW + Total Curtailment_MW) * 100
    """
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    curt_sum = float(filtered_df["Curtailment_MW"].sum()) if "Curtailment_MW" in filtered_df.columns else 0.0
    re_sum = float(filtered_df["RES_Generation_MW"].sum()) if "RES_Generation_MW" in filtered_df.columns else 0.0
    
    avg_curt_pct = float(filtered_df["Curtailment_Percent"].mean()) if "Curtailment_Percent" in filtered_df.columns else 0.0
    
    total_potential_re = re_sum + curt_sum
    macro_ratio = (curt_sum / total_potential_re * 100) if total_potential_re > 0 else 0.0
    generation_curtailed_ratio = (curt_sum / re_sum * 100) if re_sum > 0 else 0.0
    
    calc_steps = (
        f"1. Total Curtailed Energy = {curt_sum:,.1f} MW\n"
        f"2. Total RE Generated = {re_sum:,.1f} MW\n"
        f"3. Potential RE Generation (Actual + Curtailed) = {total_potential_re:,.1f} MW\n"
        f"4. Curtailment Share of Potential RE = ({curt_sum:,.1f} / {total_potential_re:,.1f}) * 100 = {macro_ratio:.2f}%\n"
        f"5. Curtailed vs Actual Generation Ratio = ({curt_sum:,.1f} / {re_sum:,.1f}) * 100 = {generation_curtailed_ratio:.2f}%\n"
        f"6. Mean of record-level Curtailment_Percent column = {avg_curt_pct:.2f}%"
    )
    
    return {
        "total_curtailment_mw": curt_sum,
        "total_re_generation_mw": re_sum,
        "total_potential_re_mw": total_potential_re,
        "macro_curtailment_share_pct": round(macro_ratio, 2),
        "curtailed_to_generation_ratio_pct": round(generation_curtailed_ratio, 2),
        "mean_record_curtailment_pct": round(avg_curt_pct, 2),
        "records_count": len(filtered_df),
        "scope": scope,
        "calculation": calc_steps
    }

def get_top_n(
    df: pd.DataFrame,
    group_col: str = "State",
    metric_col: str = "Curtailment_MW",
    n: int = 5,
    ascending: bool = False,
    agg: str = "sum",
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ranks entities (States, Regions, Causes) by aggregated metric.
    """
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    if group_col not in filtered_df.columns:
        return {"error": f"Grouping column '{group_col}' not found."}
    if metric_col not in filtered_df.columns:
        return {"error": f"Metric column '{metric_col}' not found."}
        
    agg_func = "mean" if agg in ["mean", "avg", "average"] else "sum"
    
    grouped = (
        filtered_df.groupby(group_col)[metric_col]
        .agg(agg_func)
        .reset_index()
        .sort_values(by=metric_col, ascending=ascending)
    )
    
    top_df = grouped.head(n)
    
    ranking_list = []
    for rank, (_, row) in enumerate(top_df.iterrows(), start=1):
        ranking_list.append({
            "rank": rank,
            "entity": row[group_col],
            "value": round(float(row[metric_col]), 2)
        })
        
    top_entity = ranking_list[0]["entity"] if ranking_list else "None"
    top_value = ranking_list[0]["value"] if ranking_list else 0.0
    
    direction = "Highest" if not ascending else "Lowest"
    calc_steps = (
        f"Grouped by '{group_col}', aggregated '{metric_col}' using '{agg_func}', "
        f"sorted {direction} -> Top {n} items selected from {len(grouped)} total categories in {scope}."
    )
    
    return {
        "direction": direction,
        "n": n,
        "group_col": group_col,
        "metric_col": metric_col,
        "agg": agg_func,
        "top_entity": top_entity,
        "top_value": top_value,
        "rankings": ranking_list,
        "table_df": top_df,
        "scope": scope,
        "calculation": calc_steps
    }

def compare_entities(
    df: pd.DataFrame,
    group_col: str,
    entity1: str,
    entity2: str,
    metric_col: str = "Curtailment_MW",
    agg: str = "mean",
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compares two entities (e.g. Maharashtra vs Gujarat, or Northern vs Western).
    Returns values, absolute difference, percentage difference, and clean interpretation.
    """
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    if group_col not in filtered_df.columns:
        return {"error": f"Grouping column '{group_col}' not found."}
    if metric_col not in filtered_df.columns:
        return {"error": f"Metric column '{metric_col}' not found."}
        
    df_e1 = filtered_df[filtered_df[group_col].str.strip().str.lower() == entity1.strip().lower()]
    df_e2 = filtered_df[filtered_df[group_col].str.strip().str.lower() == entity2.strip().lower()]
    
    if df_e1.empty:
        return {"error": f"Entity '{entity1}' has no records in the current dataset scope ({scope})."}
    if df_e2.empty:
        return {"error": f"Entity '{entity2}' has no records in the current dataset scope ({scope})."}
        
    agg_func = "sum" if agg.lower() in ["sum", "total"] else "mean"
    
    val1 = float(df_e1[metric_col].agg(agg_func))
    val2 = float(df_e2[metric_col].agg(agg_func))
    
    abs_diff = round(abs(val1 - val2), 2)
    min_val = min(val1, val2)
    pct_diff = round((abs_diff / min_val * 100), 2) if min_val > 0 else 0.0
    
    higher_entity = entity1 if val1 > val2 else entity2
    lower_entity = entity2 if val1 > val2 else entity1
    
    interpretation = (
        f"{higher_entity} has higher {agg_func} {metric_col} ({max(val1, val2):,.2f}) compared to "
        f"{lower_entity} ({min(val1, val2):,.2f}), representing an absolute difference of {abs_diff:,.2f} "
        f"({pct_diff:.1f}% higher)."
    )
    
    comparison_table = pd.DataFrame([
        {group_col: entity1, f"{agg_func.capitalize()}_{metric_col}": round(val1, 2), "Records": len(df_e1)},
        {group_col: entity2, f"{agg_func.capitalize()}_{metric_col}": round(val2, 2), "Records": len(df_e2)}
    ])
    
    calc_steps = (
        f"1. {entity1} ({len(df_e1):,} records): {agg_func}({metric_col}) = {val1:,.2f}\n"
        f"2. {entity2} ({len(df_e2):,} records): {agg_func}({metric_col}) = {val2:,.2f}\n"
        f"3. Absolute Difference = |{val1:,.2f} - {val2:,.2f}| = {abs_diff:,.2f}\n"
        f"4. Percentage Difference = ({abs_diff:,.2f} / {min_val:,.2f}) * 100 = {pct_diff:.1f}%"
    )
    
    return {
        "group_col": group_col,
        "entity1": entity1,
        "val1": round(val1, 2),
        "count1": len(df_e1),
        "entity2": entity2,
        "val2": round(val2, 2),
        "count2": len(df_e2),
        "metric_col": metric_col,
        "agg": agg_func,
        "abs_diff": abs_diff,
        "pct_diff": pct_diff,
        "higher_entity": higher_entity,
        "lower_entity": lower_entity,
        "interpretation": interpretation,
        "table_df": comparison_table,
        "scope": scope,
        "calculation": calc_steps
    }

def compare_metrics(
    df: pd.DataFrame,
    metrics: List[str] = ["Demand_MW", "RES_Generation_MW", "Curtailment_MW"],
    agg: str = "sum",
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Compares totals or averages across multiple metrics (e.g. Demand vs Generation vs Curtailment)."""
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    agg_func = "mean" if agg.lower() in ["mean", "avg", "average"] else "sum"
    results = {}
    
    for m in metrics:
        if m in filtered_df.columns:
            results[m] = round(float(filtered_df[m].agg(agg_func)), 2)
            
    if not results:
        return {"error": "None of the specified metrics were found in the dataset."}
        
    sorted_metrics = sorted(results.items(), key=lambda x: x[1], reverse=True)
    highest_metric, highest_val = sorted_metrics[0]
    
    table_df = pd.DataFrame([{"Metric": k, f"{agg_func.capitalize()}_Value": v} for k, v in results.items()])
    
    calc_steps = f"Aggregated [{', '.join(results.keys())}] using '{agg_func}' over {len(filtered_df):,} records in {scope}."
    
    return {
        "agg": agg_func,
        "metrics_values": results,
        "highest_metric": highest_metric,
        "highest_val": highest_val,
        "table_df": table_df,
        "scope": scope,
        "calculation": calc_steps
    }

def time_series_analysis(
    df: pd.DataFrame,
    date_col: str = "Date",
    metric_col: str = "Curtailment_MW",
    agg: str = "sum",
    freq: str = "M",
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Performs monthly or annual time-series aggregation for trend detection.
    """
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    filtered_df = sanitize_dataframe_dates(filtered_df)
    
    if "Date_dt" not in filtered_df.columns or filtered_df["Date_dt"].dropna().empty:
        return {"error": "The dataset does not contain a valid Date column for time-series analysis."}
    if metric_col not in filtered_df.columns:
        return {"error": f"Metric column '{metric_col}' not found."}
        
    agg_func = "mean" if agg.lower() in ["mean", "avg", "average"] else "sum"
    
    df_valid = filtered_df.dropna(subset=["Date_dt", metric_col]).copy()
    
    if freq.upper() == "Y":
        df_valid["Period"] = df_valid["Date_dt"].dt.to_period("Y").dt.to_timestamp()
        period_format = "%Y"
    elif freq.upper() == "Q":
        df_valid["Period"] = df_valid["Date_dt"].dt.to_period("Q").dt.to_timestamp()
        period_format = "%Y-Q%q"
    else:  # Monthly default
        df_valid["Period"] = df_valid["Date_dt"].dt.to_period("M").dt.to_timestamp()
        period_format = "%b %Y"
        
    ts_df = df_valid.groupby("Period")[metric_col].agg(agg_func).reset_index()
    ts_df = ts_df.sort_values(by="Period")
    
    if ts_df.empty:
        return {"error": "No time series points could be aggregated."}
        
    # Peak and lowest periods
    peak_row = ts_df.loc[ts_df[metric_col].idxmax()]
    low_row = ts_df.loc[ts_df[metric_col].idxmin()]
    
    peak_period_str = peak_row["Period"].strftime("%B %Y")
    low_period_str = low_row["Period"].strftime("%B %Y")
    
    calc_steps = (
        f"Converted Date to datetime, grouped into monthly intervals ({len(ts_df)} periods), "
        f"computed '{agg_func}' of '{metric_col}'. Peak occurred in {peak_period_str} ({peak_row[metric_col]:,.1f} MW)."
    )
    
    return {
        "freq": freq,
        "metric_col": metric_col,
        "agg": agg_func,
        "peak_period": peak_period_str,
        "peak_value": round(float(peak_row[metric_col]), 2),
        "lowest_period": low_period_str,
        "lowest_value": round(float(low_row[metric_col]), 2),
        "periods_count": len(ts_df),
        "time_series_df": ts_df,
        "scope": scope,
        "calculation": calc_steps
    }

def cause_analysis(
    df: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyzes the frequency and percentage breakdown of Cause_Label.
    """
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    if "Cause_Label" not in filtered_df.columns:
        return {"error": "Column 'Cause_Label' is not present in the current dataset."}
        
    cause_counts = filtered_df["Cause_Label"].value_counts(dropna=False).reset_index()
    cause_counts.columns = ["Cause_Label", "Count"]
    
    total_causes = cause_counts["Count"].sum()
    cause_counts["Percentage"] = (cause_counts["Count"] / total_causes * 100).round(2)
    
    primary_cause = cause_counts.iloc[0]["Cause_Label"]
    primary_count = int(cause_counts.iloc[0]["Count"])
    primary_pct = float(cause_counts.iloc[0]["Percentage"])
    
    distribution_dict = {}
    for _, row in cause_counts.iterrows():
        distribution_dict[row["Cause_Label"]] = {
            "count": int(row["Count"]),
            "pct": float(row["Percentage"])
        }
        
    calc_steps = (
        f"Grouped by 'Cause_Label' across {total_causes:,} records. "
        f"Most frequent cause: '{primary_cause}' with {primary_count:,} events ({primary_pct:.1f}%)."
    )
    
    return {
        "total_records": total_causes,
        "primary_cause": primary_cause,
        "primary_count": primary_count,
        "primary_pct": primary_pct,
        "distribution": distribution_dict,
        "table_df": cause_counts,
        "scope": scope,
        "calculation": calc_steps
    }

def correlation_analysis(
    df: pd.DataFrame,
    col1: str = "Demand_MW",
    col2: str = "Curtailment_MW",
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes Pearson correlation coefficient between two numeric fields.
    """
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    if col1 not in filtered_df.columns or col2 not in filtered_df.columns:
        return {"error": f"Columns '{col1}' or '{col2}' not found in dataset."}
        
    valid_data = filtered_df[[col1, col2]].dropna()
    if len(valid_data) < 2:
        return {"error": "Insufficient data points to compute correlation."}
        
    r = float(valid_data[col1].corr(valid_data[col2]))
    
    # Interpretation
    abs_r = abs(r)
    strength = "very strong" if abs_r >= 0.8 else ("strong" if abs_r >= 0.6 else ("moderate" if abs_r >= 0.4 else ("weak" if abs_r >= 0.2 else "negligible")))
    direction = "positive" if r > 0 else "negative"
    
    interpretation = (
        f"The Pearson correlation between {col1} and {col2} is {r:.3f}, indicating a {strength} {direction} correlation. "
    )
    if direction == "negative":
        interpretation += f"As {col1} increases, {col2} tends to decrease."
    else:
        interpretation += f"As {col1} increases, {col2} tends to increase as well."
        
    calc_steps = f"Pearson r = cov({col1}, {col2}) / (std({col1}) * std({col2})) = {r:.4f} across {len(valid_data):,} observations in {scope}."
    
    return {
        "col1": col1,
        "col2": col2,
        "r": round(r, 4),
        "strength": strength,
        "direction": direction,
        "interpretation": interpretation,
        "sample_size": len(valid_data),
        "scope": scope,
        "calculation": calc_steps
    }

def search_remarks(
    df: pd.DataFrame,
    keyword: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Searches Dispatcher_Remark_Synthetic for specific keywords."""
    filtered_df, scope_list = apply_filters(df, **(filters or {}))
    scope = scope_list[0]
    
    if filtered_df.empty:
        return {"error": f"No records found matching filters ({scope}).", "scope": scope}
        
    remark_col = "Dispatcher_Remark_Synthetic" if "Dispatcher_Remark_Synthetic" in filtered_df.columns else (
        "dispatcher_remark" if "dispatcher_remark" in filtered_df.columns else None
    )
    
    if not remark_col:
        return {"error": "No dispatcher remark column found in the loaded dataset."}
        
    mask = filtered_df[remark_col].astype(str).str.contains(keyword, case=False, na=False)
    matches_df = filtered_df[mask]
    
    total_matches = len(matches_df)
    results = matches_df.head(limit)
    
    calc_steps = f"Filtered {len(filtered_df):,} records where '{remark_col}' contains '{keyword}' (case-insensitive) -> Found {total_matches:,} matches in {scope}."
    
    return {
        "keyword": keyword,
        "total_matches": total_matches,
        "returned_count": len(results),
        "table_df": results,
        "scope": scope,
        "calculation": calc_steps
    }

def predict_remark_cause(
    text: str,
    classifier=None
) -> Dict[str, Any]:
    """
    Uses the project's CurtailmentRemarkClassifier (TF-IDF + LogisticRegression)
    to classify a dispatcher remark and extract confidence distribution.
    """
    if not text or not text.strip():
        return {"error": "Please provide a dispatcher remark text to analyze."}
        
    if classifier is None:
        # Load or train on demand
        try:
            from agents.analyst.classifier import CurtailmentRemarkClassifier
            clf = CurtailmentRemarkClassifier()
            # Check if synthetic CSV exists for training
            import os
            train_path = "data/processed/synthetic_curtailment_events.csv"
            if os.path.exists(train_path):
                train_df = pd.read_csv(train_path)
                clf.train_and_evaluate(train_df)
                classifier = clf
        except Exception as e:
            return {"error": f"ML Classifier could not be initialized: {str(e)}"}
            
    if classifier is None or not getattr(classifier, "is_trained", False):
        return {"error": "Classifier is not trained or model weights are unavailable."}
        
    try:
        pipeline = classifier.pipeline
        probs = pipeline.predict_proba([text])[0]
        classes = pipeline.classes_
        
        prob_dict = {str(c): round(float(p) * 100, 1) for c, p in zip(classes, probs)}
        max_idx = int(np.argmax(probs))
        predicted_cause = str(classes[max_idx])
        confidence_pct = round(float(probs[max_idx]) * 100, 1)
        
        needs_review = confidence_pct < 60.0  # Brain Rule 3: < 60% needs review
        
        calc_steps = (
            f"1. Vectorized text using TfidfVectorizer(ngram_range=(1,2))\n"
            f"2. Evaluated using balanced LogisticRegression model\n"
            f"3. Class probabilities: {prob_dict}\n"
            f"4. Selected class: '{predicted_cause}' with {confidence_pct:.1f}% confidence"
        )
        
        return {
            "remark": text,
            "predicted_cause": predicted_cause,
            "confidence_pct": confidence_pct,
            "all_probabilities": prob_dict,
            "needs_review": needs_review,
            "pipeline_status": "needs_review" if needs_review else "classified",
            "calculation": calc_steps
        }
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}

def compliance_analysis(
    compliance_df: pd.DataFrame,
    events_df: pd.DataFrame,
    query_type: str = "summary",
    region: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes regulatory compliance scorecards and anomaly audit flags.
    Reuses logic from agents/warden/compliance.py without inventing rules.
    """
    # If compliance_df is empty, try loading it from data/processed
    if compliance_df.empty:
        import os
        comp_path = "data/processed/compliance_scorecard.csv"
        if os.path.exists(comp_path):
            compliance_df = pd.read_csv(comp_path)
            
    # Also load classified events if available for flagged events audit
    import os
    classified_path = "data/processed/classified_curtailment_events.csv"
    classified_df = pd.DataFrame()
    if os.path.exists(classified_path):
        classified_df = pd.read_csv(classified_path)
        
    if compliance_df.empty and classified_df.empty:
        # Fallback to computing compliance on events_df if possible
        if not events_df.empty and "curtailed_mw" in events_df.columns:
            from agents.warden.compliance import compute_compliance_scorecard
            compliance_df = compute_compliance_scorecard(events_df, output_path=None)
            
    if compliance_df.empty and classified_df.empty:
        return {
            "error": "The regulatory compliance scorecard is not yet computed. Run the Warden compliance pipeline first."
        }
        
    # Flagged records in classified_df (e.g. mismatch or needs_review)
    flagged_df = pd.DataFrame()
    total_flagged = 0
    if not classified_df.empty:
        flag_mask = (classified_df["validation_status"] == "mismatch") | (classified_df["pipeline_status"] == "needs_review")
        flagged_df = classified_df[flag_mask]
        total_flagged = len(flagged_df)
        
    calc_steps = (
        f"Evaluated regulatory compliance records against CERC/IEGC disclosure standards:\n"
        f"• Completeness weight: 40%\n"
        f"• Cross-validation match weight: 30%\n"
        f"• Timeliness weight: 30%\n"
        f"Total flagged audit anomalies identified: {total_flagged:,} events."
    )
    
    return {
        "compliance_scorecard_df": compliance_df,
        "flagged_events_df": flagged_df.head(10),
        "total_flagged_events": total_flagged,
        "total_audited_regions": len(compliance_df),
        "avg_composite_score": round(float(compliance_df["composite_compliance_score"].mean()), 1) if "composite_compliance_score" in compliance_df.columns else 0.0,
        "calculation": calc_steps
    }
