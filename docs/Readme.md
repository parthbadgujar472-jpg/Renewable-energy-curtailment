# Renewable Energy Curtailment Analysis and Regulatory Compliance System

**FF No. 180 · Group 11 · IT Dept, Sem 03 · Guide: Dr. Pankaj Kunekar**

An automated pipeline that collects, standardizes, classifies, and cross-validates India's renewable energy curtailment data from scattered RLDC/SLDC/CEA portals — and audits whether reporting meets regulatory disclosure requirements.

---

## Why this exists

India curtails solar and wind generation regularly for grid-security and (sometimes) commercial reasons, but the data explaining *when, why, and how much* is scattered across dozens of regional portals in inconsistent formats, with unstructured dispatcher notes as the only explanation for each event. This project builds the missing open, reproducible dataset — and a way to check whether the reported reasons actually hold up against real generation data.

## What it does

1. **Scrapes** daily curtailment/generation reports from RLDC, SLDC, and CEA public portals.
2. **Extracts** structured data from PDFs (including scanned/OCR'd ones) and HTML/Excel reports.
3. **Classifies** dispatcher remarks into standardized causes (Grid Security / High Frequency / Commercial / etc.) using NLP.
4. **Cross-validates** reported curtailment against independent schedule-vs-actual generation deviation data.
5. **Scores** each region's regulatory disclosure compliance (timeliness, completeness).
6. **Serves** everything via a REST API, CSV export, and an interactive Streamlit dashboard.

See `Architecture.md` for how it's built, `Agent.md` for who's building what, `PRD.md` for what "done" looks like, and `Decisions.md` for why key choices were made.

## Tech stack

- **Language:** Python
- **Scraping:** `requests`, `BeautifulSoup`
- **Scheduling:** `APScheduler`
- **PDF/OCR:** `pdfplumber`, `PyPDF2`, `pytesseract` (Tesseract OCR)
- **Data processing:** `pandas`, `NumPy`
- **Database:** PostgreSQL via `SQLAlchemy`
- **NLP:** `scikit-learn` (TF-IDF + Logistic Regression / SVM)
- **API:** `FastAPI` + `Pydantic`
- **Dashboard:** `Streamlit` + `Plotly`
- **Distribution:** CSV export for open access

## Project structure (proposed)

```
.
├── docs/
│   ├── Brain.md
│   ├── Agent.md
│   ├── PRD.md
│   ├── Architecture.md
│   ├── Decisions.md
│   └── Readme.md
├── agents/
│   ├── scout/           # Agent 1 — scraping & ingestion
│   ├── refinery/         # Agent 2 — parsing, OCR, normalization
│   ├── analyst/           # Agent 3 — NLP classification, cross-validation
│   └── warden/            # Agent 4 — compliance scoring, API
├── data/
│   ├── raw/               # untouched downloaded source files
│   └── processed/         # normalized outputs (pre-DB, for debugging)
├── api/                   # FastAPI app
├── dashboard/             # Streamlit app
├── config/
│   └── portal_registry.yaml   # RLDC/SLDC/CEA source URLs + formats
└── tests/
```

## Getting started (once code exists)

```bash
# clone and set up environment
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# set up PostgreSQL and run migrations
# (connection string in .env — see Architecture.md for schema)

# run one ingestion cycle manually
python -m agents.scout.run

# start the API
uvicorn api.main:app --reload

# start the dashboard
streamlit run dashboard/app.py
```

## Current status

This is a semester project (FF180) under active development. Progress is tracked against the milestones in `PRD.md` §7 and reviewed against the phased approach described in the project synopsis (portal discovery → scraping → parsing → NLP → cross-validation → compliance/API → dashboard).

## References

Key literature and regulatory sources underpinning this project are cited in the project synopsis, including Bird et al. (2016) on international curtailment experience, the NREL/LBNL "Greening the Grid" study on India's RE integration, and the CERC/IEGC and Forum of Regulators guidelines on curtailment disclosure.
