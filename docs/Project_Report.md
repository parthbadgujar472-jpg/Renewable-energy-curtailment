# Project Report: RE Curtailment Analytics & Regulatory Compliance

This document provides a comprehensive explanation of the dataset, the technical decisions made (including the use of NLP and ML Pipelines), the foundation of the synthetic data generation, the division of labor among the four team members, and the future scope of the project.

---

## 1. Dataset Explanation

The dataset used in this project represents **Renewable Energy (RE) Curtailment** records across various Indian states and regions. It tracks the amount of renewable energy (Solar, Wind, etc.) that was generated versus the amount that was curtailed (wasted or not fed into the grid) due to various grid constraints.

**Key Features of the Dataset:**
- **Temporal & Spatial Data:** `Date`, `Region` (Northern, Western, Southern, etc.), and `State`.
- **Power Metrics:** `Demand_MW` (total power demand), `RES_Generation_MW` (total renewable energy generated), `Curtailment_MW` (amount of energy curtailed), and `Curtailment_Percent` (percentage of generated energy that was curtailed).
- **Categorical & Text Data:** 
  - `Dispatcher_Remark_Synthetic`: Text notes representing instructions or remarks logged by State Load Dispatch Centers (SLDCs).
  - `Cause_Label`: The standardized reason for curtailment (e.g., *Transmission Congestion, Grid Instability, Low Demand, Over-generation*).
- **Metadata:** `is_synthetic_label` (boolean flag to track if the record is synthetically generated or real).

### 1.1 On What Basis Was the Synthetic Dataset Created?

Historical curtailment data in India (from CEA / POSOCO) is often scarce, highly aggregated, or not publicly available at a granular daily level with detailed dispatcher remarks. To build and test a robust analytics system, we generated a **Synthetic Dataset** based on the following real-world principles:

1. **Grid Physics & Seasonal Trends:** Demand and renewable generation values were generated to mimic actual seasonal behaviors (e.g., high wind generation during monsoons, high solar during summer).
2. **Realistic Curtailment Ratios:** Curtailment percentages were kept within realistic historical bounds (typically 1% to 15%), spiking during periods where RE generation vastly exceeded local demand or during simulated grid events.
3. **Regional Skews:** Certain regions (like the Northern and Western grids) were programmed to experience more *Transmission Congestion* due to high RE capacity but limited evacuation infrastructure, accurately reflecting India's current grid realities.
4. **Synthetic Text Generation:** Dispatcher remarks were procedurally generated using realistic templates (e.g., *"Reduce solar by 50MW due to line overloading"*). This provided the necessary unstructured text data to train and test our NLP models.

---

## 2. Technical Justifications: Why NLP and Pipelines?

Our guide required a rigorous technical approach to handling data. Here is the justification for the specific technologies used:

### 2.1 Why NLP (Natural Language Processing)?
In real-world grid operations, SLDCs (State Load Dispatch Centers) do not always select a neat dropdown option when curtailing energy. They write free-text logs and remarks (e.g., *"Voltage high at 400kV substation, back down wind"*). 
- **The Problem:** We cannot perform structured data analytics, filtering, or compliance checking on raw, messy text.
- **The Solution (NLP):** We used NLP to "read" these dispatcher remarks and automatically classify them into standardized buckets (`Cause_Label` like *Grid Instability*). We utilized **TF-IDF (Term Frequency-Inverse Document Frequency)** to vectorize the text, allowing the machine learning model to understand which words (like "voltage", "trip", "frequency") strongly correlate with specific grid issues.

### 2.2 Why Scikit-Learn Pipelines?
When building the text classification model, we combined the TF-IDF Vectorizer and the Logistic Regression classifier into a single **Scikit-Learn Pipeline**.
- **Data Leakage Prevention:** Pipelines ensure that the TF-IDF vocabulary is only learned from the training data. If we vectorized the whole dataset before splitting, information from the test set would "leak" into the training phase, artificially inflating accuracy.
- **Reproducibility & Deployment:** A pipeline bundles the preprocessing steps and the model into a single object. When the Streamlit dashboard receives a new dispatcher remark, we only have to call `pipeline.predict()`. Without a pipeline, we would have to manually save, load, and apply the vectorizer and the model separately, which is error-prone and messy.

---

## 3. Division of Work (4 Persons)

To execute this complex system, the work was divided logically among four team members, simulating a real-world data science and engineering squad.

### Person 1: Data Engineer (Data Acquisition & Synthetic Generation)
- **Approach:** Focused on the foundational data layer. Since real data is scarce, this person was responsible for designing the statistical distributions and scripts that generated the synthetic multi-year dataset.
- **Execution:** Wrote Python scripts (`synthetic_data_generator.py`) using `pandas` and `numpy` to generate realistic time-series data, ensuring the data respected grid logic (e.g., Curtailment MW cannot exceed Generation MW). Generated the realistic dispatcher text remarks based on predefined operational templates.

### Person 2: Machine Learning Engineer (NLP & Cause Classification)
- **Approach:** Focused on making sense of the unstructured text data generated by Person 1. Needed a lightweight, highly interpretable model suitable for tabular dashboard deployment.
- **Execution:** Developed `classifier.py`. Built the Scikit-Learn Pipeline using TF-IDF and Logistic Regression. Handled train-test splits, evaluated the model using confusion matrices and classification reports, and exported the trained model using `joblib` so it could be consumed by the dashboard without retraining.

### Person 3: Domain / Compliance Analyst (Regulatory Rules Engine)
- **Approach:** Focused on the business logic and regulatory aspect of the project. Needed to ensure the system didn't just show data, but actually audited it against CEA/POSOCO grid codes.
- **Execution:** Developed the `compliance.py` module. Wrote rule-based algorithms to flag anomalies—for example, flagging instances where curtailment exceeded permissible limits without a valid "Grid Security" justification in the dispatcher remarks.

### Person 4: Frontend & BI Developer (Streamlit Dashboard)
- **Approach:** Focused on UI/UX and stakeholder presentation. The goal was to create a "Grid Control Room" aesthetic that combined all the backend work into an interactive, visually stunning platform.
- **Execution:** Developed `app.py`. Used Streamlit for the framework and custom CSS for the dark-mode, neon-accented UI. Used Plotly for interactive charts (time-series lines, regional bar charts, state-level scatter plots). Integrated the data outputs from Persons 1, 2, and 3 into the final unified dashboard.

---

## 4. Future Additions (What We Will Add Next)

As the project scales, we plan to implement the following enhancements to satisfy strict enterprise and academic requirements:

1. **Real-Time API Integration:** Transitioning away from static `.xlsx` files by building a REST API (using FastAPI or Flask) that simulates a live data feed from SLDC sensors, updating the dashboard in real-time.
2. **Advanced Deep Learning for NLP:** Upgrading the current TF-IDF + Logistic Regression model to a modern transformer-based LLM (like a fine-tuned BERT or small Llama model) to better understand complex, multi-sentence dispatcher remarks and regional linguistic nuances.
3. **Forecasting Models:** Implementing Time-Series forecasting (using ARIMA, Prophet, or LSTMs) to predict *future* curtailment events 24 to 48 hours in advance based on weather forecasts and demand patterns.
4. **Automated Alert System:** Adding an SMTP/Email or Webhook integration that automatically sends a high-priority alert to regulators if the system detects illegal curtailment (e.g., curtailment happening purely for commercial reasons rather than grid security).
