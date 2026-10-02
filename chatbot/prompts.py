"""
Domain Knowledge, Educational Answers, System Prompts, and Disclaimers
for RE Curtailment Analytics & Regulatory Compliance Chatbot.
"""

# ── General Energy & Grid Domain Knowledge Base ──────────────────────────────
DOMAIN_DEFINITIONS = {
    "curtailment": (
        "**Renewable Energy Curtailment** is the deliberate reduction of output from wind or solar "
        "generating facilities below what they could have produced with available resources. "
        "Grid operators (SLDCs/RLDCs) issue curtailment or backing down directives when transmitting all "
        "generated power would violate transmission limits, risk grid frequency violations, or exceed demand."
    ),
    "grid_instability": (
        "**Grid Instability (or Grid Security Constraint)** occurs when dynamic grid variables—such as voltage, "
        "reactive power, or system frequency—deviate outside safe statutory operating limits (e.g., 49.90 Hz – 50.05 Hz "
        "under Indian IEGC grid code). Grid operators instruct RE generators to back down to avoid blackout conditions."
    ),
    "transmission_congestion": (
        "**Transmission Congestion (or Transmission Constraint)** occurs when power scheduled across a transmission "
        "corridor or substation bay exceeds its physical thermal carrying capacity or N-1 security limits. "
        "Even if generation is clean and cheap, power cannot reach demand centers without overloading lines."
    ),
    "over_generation": (
        "**Over-generation (or High System Frequency)** occurs when total electrical generation nationwide "
        "surpasses real-time consumer demand. Because electricity cannot easily be stored at scale on the grid, "
        "excess generation accelerates turbine rotational speed and pushes grid frequency above 50.05 Hz. "
        "Curtailing RE is an immediate tool dispatchers use to arrest frequency runaway."
    ),
    "commercial_discom": (
        "**Commercial / DISCOM Request (Low Demand)** occurs when power distribution companies (DISCOMs) "
        "request backing down due to temporary drops in local power demand (e.g., agricultural feeder shutdowns, "
        "cool weather, or factory closures), or due to off-peak commercial merit order dispatch economic optimization."
    ),
    "mw_vs_mwh": (
        "**MW (Megawatt) vs MWh (Megawatt-Hour)**:\n"
        "• **MW (Megawatt)** is a unit of **Power** (the instantaneous rate of energy flow/capacity). "
        "1 MW = 1,000 Kilowatts (kW) = 1,000,000 Watts.\n"
        "• **MWh (Megawatt-Hour)** is a unit of **Energy** (the total volume of power produced or consumed over time). "
        "Running a 1 MW solar plant at full capacity for 1 hour produces 1 MWh (1,000 units/kWh) of electrical energy."
    ),
    "mw": (
        "**MW (Megawatt)** measures instantaneous electrical power capacity. "
        "1 MW = 1,000 kW = 1,000,000 Watts. In India, a typical 1 MW solar plant requires roughly 3 to 4 acres of land "
        "and generates around 4,000 units (kWh) of electricity per sunny day."
    ),
    "rooftop_solar": (
        "**Rooftop Solar** consists of photovoltaic (PV) solar panels mounted on building roofs to generate clean electricity "
        "directly at the point of consumption. In India, under net metering or gross metering with DISCOMs, "
        "surplus power produced during the day is exported to the grid, earning energy credits that offset monthly electricity bills."
    ),
    "renewable_energy": (
        "**Renewable Energy (RE)** is energy derived from natural replenishment sources like solar irradiance, wind, "
        "biomass, small hydro, and geothermal. In India, the Central Electricity Authority (CEA) tracks utility-scale "
        "RES (Renewable Energy Sources) to support the national 500 GW non-fossil capacity target by 2030."
    ),
    "dispatcher_remark": (
        "**Dispatcher Remarks** are real-time logbook entries entered by State / Regional Load Despatch Centre (SLDC/RLDC) "
        "shift engineers explaining why a generator was ordered to back down. In this dashboard, synthetic natural-language "
        "remarks simulate real SLDC logbook patterns to train and evaluate NLP cause-classification pipelines."
    ),
    "project_overview": (
        "This project, **RE Curtailment Analytics & Regulatory Compliance**, is an intelligent auditing platform for "
        "Indian power grid operations. It combines CEA/POSOCO historical demand and generation baselines with "
        "machine learning cause classification (TF-IDF + Logistic Regression) and regulatory compliance scorecards "
        "aligned with CERC/IEGC disclosure standards."
    )
}

# ── Consumer Energy Guidance ─────────────────────────────────────────────────
CONSUMER_TIPS = {
    "reduce_bill": (
        "### 💡 Practical Ways to Lower Your Household Electricity Bill:\n\n"
        "1. **Adopt Rooftop Solar**: Generate your own power during daytime and take advantage of the *PM Surya Ghar Muft Bijli Yojana* subsidy (up to ₹78,000 for 3 kW).\n"
        "2. **Shift High-Power Appliances**: Run heavy loads (washing machines, water heaters, EV charging, pool pumps) during peak solar hours (10:00 AM – 3:00 PM) when grid power has maximum solar penetration.\n"
        "3. **Upgrade to 5-Star Inverter Appliances**: Inverter air conditioners, BLDC ceiling fans (which consume 28W vs 75W regular), and 5-star refrigerators reduce cooling/running load by 30–50%.\n"
        "4. **Smart Thermostat Management**: Set AC temperatures to 24°C–26°C. Every 1°C increase saves roughly 6% in cooling electricity consumption.\n"
        "5. **Eliminate Phantom Loads**: Turn off microwave, TV, and computer extension cords at the socket when not in use."
    ),
    "solar_benefits": (
        "### ☀️ Benefits of Rooftop Solar for Households in India:\n\n"
        "• **Substantial Bill Reduction**: Can eliminate 70% to 90% of your monthly power bill via net-metering.\n"
        "• **Government Subsidies**: Under PM Surya Ghar Yojana, central subsidies provide ₹30,000 for 1 kW, ₹60,000 for 2 kW, and ₹78,000 for 3 kW+ systems.\n"
        "• **Attractive Payback**: Typical payback period in Indian metros is 3.5 to 5 years, with solar panels guaranteed for 25 years.\n"
        "• **Grid Support**: Daytime solar generation reduces peak thermal load on local distribution transformers."
    ),
    "solar_grid_impact": (
        "### ⚡ How Solar Generation Affects the Electric Grid:\n\n"
        "Solar generation peaks sharply between 11:00 AM and 2:00 PM (the 'solar noon hump').\n"
        "• **The Benefit**: It offsets expensive daytime peak thermal power generation and lowers transmission line heating.\n"
        "• **The Challenge**: As evening arrives and solar generation ramps down while household lighting/AC loads ramp up, "
        "the grid experiences a steep ramp demand known as the **'Duck Curve'**. Without storage or flexible balancing, "
        "excess solar during midday may sometimes be curtailed to prevent grid instability."
    ),
    "when_is_re_peak": (
        "### 🕐 Peak Renewable Generation Hours in India:\n\n"
        "• **Solar Generation**: Peaks strictly during midday hours (**10:30 AM – 2:30 PM**) across states like Rajasthan, Gujarat, and Tamil Nadu.\n"
        "• **Wind Generation**: Strongly seasonal. Peaks during the **Southwest Monsoon (May to September)**, with generation sustained across late afternoons and late nights in coastal/wind corridors (Gujarat, Tamil Nadu, Karnataka)."
    )
}

# ── Transparency & Disclaimer Templates ──────────────────────────────────────
DISCLAIMER_SYNTHETIC = (
    "\n\n> ⚠️ **Data Notice**: Curtailment events and dispatcher remarks in this dataset are modeled synthetic "
    "estimates derived from CEA/POSOCO generation baselines for educational and research audit purposes."
)

DISCLAIMER_UNAVAILABLE = (
    "I don't have enough information in the current dataset to answer that question. "
    "The loaded dataset contains Indian renewable energy curtailment and generation records from 2022 to July 2026 "
    "covering 36 states/UTs with Demand_MW, RES_Generation_MW, Curtailment_MW, Curtailment_Percent, and Cause_Labels. "
    "Please ask a question related to these metrics or the project's ML/compliance systems."
)

# ── LLM System Prompt ────────────────────────────────────────────────────────
LLM_SYSTEM_PROMPT = """
You are the "AI Energy Intelligence Assistant" for the Indian Renewable Energy Curtailment & Regulatory Compliance system.
Your job is to explain power grid analytics, curtailment events, machine learning cause classification, and regulatory compliance to grid engineers, policymakers, and common consumers.

CRITICAL RULES:
1. NEVER INVENT OR HALLUCINATE NUMERICAL DATA. All statistics, sums, averages, rankings, dates, and percentages must come solely from the supplied Python/pandas calculation payload.
2. If data is missing or marked unavailable in the payload, explicitly state that the dataset does not contain that information.
3. Distinguish clearly between:
   - Facts directly calculated from the dataset.
   - Project architecture / ML classifier insights.
   - General electrical engineering principles.
4. Keep answers professional, concise (2-4 sentences for simple queries, structured markdown with bullet points for multi-metric queries).
5. Always mention that curtailment data in this project is modeled synthetic estimation built upon CEA/POSOCO actual generation baselines.
"""
