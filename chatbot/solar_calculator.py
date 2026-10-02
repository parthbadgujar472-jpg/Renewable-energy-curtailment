"""
Consumer Electricity Assistant & Rooftop Solar Savings Calculator.
Implements standard Indian insolation models and PM Surya Ghar Muft Bijli Yojana subsidy logic.
"""

from typing import Dict, Any, Optional

# Average electricity tariffs by Indian state (residential indicative, INR/unit)
STATE_TARIFF_MAP = {
    "Maharashtra": 8.50,
    "Gujarat": 6.80,
    "Rajasthan": 7.50,
    "Tamil Nadu": 6.50,
    "Karnataka": 7.80,
    "Delhi": 5.00,
    "Uttar Pradesh": 7.20,
    "Madhya Pradesh": 7.00,
    "Haryana": 6.90,
    "Punjab": 6.20,
    "West Bengal": 8.20,
    "Andhra Pradesh": 7.10,
    "Telangana": 7.30,
    "Kerala": 6.70,
    "Bihar": 6.80,
}
DEFAULT_TARIFF = 7.00  # INR/unit nationwide benchmark

# Benchmark installation cost: ~₹55,000 / kWp
BENCHMARK_COST_PER_KW = 55000.0

# 1 kW needs ~100 sq ft shadow-free rooftop area
SQ_FT_PER_KW = 100.0

# In India, 1 kWp produces ~4.0 units (kWh) per day average (120 units/month, 1440 units/year)
UNITS_PER_KW_PER_DAY = 4.0
UNITS_PER_KW_PER_MONTH = 120.0
UNITS_PER_KW_PER_YEAR = 1440.0

# Emission factor: ~0.82 kg CO2 per kWh avoided in Indian thermal-dominant grid
CO2_KG_PER_KWH = 0.82

def compute_pm_surya_ghar_subsidy(kw: float) -> float:
    """
    Computes Central Government subsidy under PM Surya Ghar Muft Bijli Yojana (2024 scheme):
    - Up to 1 kW: ₹30,000
    - Up to 2 kW: ₹60,000
    - 3 kW and above: ₹78,000 (capped at ₹78,000 for residential single connections)
    """
    if kw <= 0:
        return 0.0
    elif kw < 1.5:
        return 30000.0
    elif kw < 2.5:
        return 60000.0
    else:
        return 78000.0

def calculate_solar_potential(
    monthly_units: float,
    state: Optional[str] = None,
    rooftop_sqft: Optional[float] = None,
    custom_tariff: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculates estimated solar sizing, generation, cost, subsidy, bill reduction, and payback.
    
    Parameters:
    - monthly_units: User's average monthly electricity consumption in kWh (units)
    - state: Optional state name to pick state-specific tariff
    - rooftop_sqft: Available shadow-free rooftop area in sq ft
    - custom_tariff: User-specified electricity tariff in INR/kWh
    """
    if monthly_units <= 0:
        monthly_units = 250.0  # sensible fallback if unspecified
        
    tariff = custom_tariff if custom_tariff and custom_tariff > 0 else STATE_TARIFF_MAP.get(state or "", DEFAULT_TARIFF)
    
    # Sizing: Recommend solar to cover ~90% of monthly consumption
    recommended_kw = max(1.0, round((monthly_units * 0.90) / UNITS_PER_KW_PER_MONTH, 1))
    
    # Roof area check
    required_area_sqft = recommended_kw * SQ_FT_PER_KW
    area_constrained = False
    if rooftop_sqft and rooftop_sqft > 0:
        max_kw_from_roof = max(1.0, round(rooftop_sqft / SQ_FT_PER_KW, 1))
        if max_kw_from_roof < recommended_kw:
            recommended_kw = max_kw_from_roof
            area_constrained = True
            
    # Generation calculations
    monthly_gen_units = round(recommended_kw * UNITS_PER_KW_PER_MONTH, 1)
    annual_gen_units = round(recommended_kw * UNITS_PER_KW_PER_YEAR, 1)
    
    # Financials
    gross_system_cost = round(recommended_kw * BENCHMARK_COST_PER_KW, 0)
    subsidy_amount = compute_pm_surya_ghar_subsidy(recommended_kw)
    net_customer_cost = max(0.0, gross_system_cost - subsidy_amount)
    
    # Bill savings (assuming full self-consumption + net metering)
    monthly_bill_before = round(monthly_units * tariff, 0)
    effective_units_offset = min(monthly_units, monthly_gen_units)
    monthly_savings = round(effective_units_offset * tariff, 0)
    annual_savings = round(monthly_savings * 12, 0)
    monthly_bill_after = max(0.0, monthly_bill_before - monthly_savings)
    
    # Payback period
    payback_years = round(net_customer_cost / annual_savings, 1) if annual_savings > 0 else 0.0
    
    # CO2 avoidance
    co2_saved_kg_year = round(annual_gen_units * CO2_KG_PER_KWH, 0)
    trees_equivalent = round(co2_saved_kg_year / 20.0, 0)  # ~20kg CO2 absorbed per mature tree/year
    
    calc_steps = (
        f"1. Target Sizing = (Monthly Units {monthly_units:.0f} * 0.90) / 120 units/kW = {recommended_kw:.1f} kW\n"
        f"2. Required Shadow-Free Rooftop Area = {recommended_kw:.1f} kW * 100 sq ft/kW = {required_area_sqft:.0f} sq ft\n"
        f"3. Monthly Clean Generation = {recommended_kw:.1f} kW * 120 units/month = {monthly_gen_units:.0f} kWh\n"
        f"4. Gross System Cost = {recommended_kw:.1f} kW * ₹55,000/kW = ₹{gross_system_cost:,.0f}\n"
        f"5. PM Surya Ghar Central Subsidy = ₹{subsidy_amount:,.0f}\n"
        f"6. Net Investment = ₹{gross_system_cost:,.0f} - ₹{subsidy_amount:,.0f} = ₹{net_customer_cost:,.0f}\n"
        f"7. Annual Savings = {monthly_gen_units:.0f} kWh * ₹{tariff:.2f}/unit * 12 months = ₹{annual_savings:,.0f}\n"
        f"8. Estimated Payback = ₹{net_customer_cost:,.0f} / ₹{annual_savings:,.0f} = {payback_years:.1f} Years"
    )
    
    summary_markdown = f"""
### ☀️ Rooftop Solar Feasibility & Savings Estimate

| Parameter | Estimated Value |
|---|---|
| **Recommended Solar Capacity** | **{recommended_kw:.1f} kW** |
| **Required Roof Area** | **~{required_area_sqft:.0f} sq. ft.** |
| **Monthly Solar Generation** | **~{monthly_gen_units:.0f} kWh (units)** |
| **Applicable Tariff Rate** | **₹{tariff:.2f} / kWh** ({state or 'Standard National Average'}) |
| **Estimated Monthly Savings** | **₹{monthly_savings:,.0f} / month** |
| **Estimated Annual Savings** | **₹{annual_savings:,.0f} / year** |
| **Gross System Cost** | **₹{gross_system_cost:,.0f}** |
| **PM Surya Ghar Subsidy** | **- ₹{subsidy_amount:,.0f}** |
| **Net Investment (After Subsidy)** | **₹{net_customer_cost:,.0f}** |
| **Estimated Payback Period** | **~{payback_years:.1f} Years** |
| **Environmental Impact** | **{co2_saved_kg_year:,.0f} kg CO₂ / yr** (~{trees_equivalent:.0f} trees planted) |

> ℹ️ *Note: This calculation uses standard Indian solar insolation (4 kWh/kWp/day) and PM Surya Ghar subsidy guidelines. Actual generation depends on panel orientation, site shading, and local DISCOM net-metering approval.*
"""
    
    return {
        "recommended_kw": recommended_kw,
        "required_area_sqft": required_area_sqft,
        "monthly_gen_units": monthly_gen_units,
        "annual_gen_units": annual_gen_units,
        "tariff": tariff,
        "monthly_bill_before": monthly_bill_before,
        "monthly_bill_after": monthly_bill_after,
        "monthly_savings": monthly_savings,
        "annual_savings": annual_savings,
        "gross_cost": gross_system_cost,
        "subsidy": subsidy_amount,
        "net_cost": net_customer_cost,
        "payback_years": payback_years,
        "co2_saved_kg_year": co2_saved_kg_year,
        "area_constrained": area_constrained,
        "calculation_steps": calc_steps,
        "summary_markdown": summary_markdown
    }
