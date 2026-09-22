# Agent.md — Multi-Agent Work Breakdown

Four agents, each owning a distinct phase of the pipeline described in the synopsis. The split is designed so **each of the 4 group members can own one agent end-to-end** — clean interfaces in, clean interfaces out, minimal shared code until integration.

---

## Agent 1 — The Scout (Data Acquisition Agent)

**Owns synopsis phases:** 1 (Portal Inventory & Format Discovery), 2 (Automated Scraping & Ingestion)

**Mission:** Find where the data lives, and reliably get the raw files onto disk every day.

**Responsibilities:**
- Maintain a **portal registry** — a config file listing every RLDC/SLDC/CEA source URL, its known report format (searchable PDF / scanned PDF / HTML table / Excel), and its typical publish time.
- Poll/scrape each portal on schedule (APScheduler), detect newly published reports vs. already-seen ones.
- Download and store raw files under a content-addressed path (e.g. `raw/{region}/{date}/{filename}`) so nothing is ever silently overwritten.
- Implement retry logic with backoff for portal downtime (grid operator sites are not highly available).
- Emit a **manifest record** per file: `{source_url, region, report_date, format_type, download_timestamp, file_hash}`.

**Primary tools:** `requests`, `BeautifulSoup`/`lxml` (HTML table scraping), `APScheduler`, simple `SQLAlchemy` writes to a `raw_documents` table.

**Also owns:** dataset research and discovery generally — this is the agent that would go looking for the CEA `gen-re.cea.gov.in` daily Excel reports, SRLDC/WRLDC/NRLDC/ERLDC/NERLDC report pages, and any new public data source worth adding to the registry. If the team is evaluating "should we add this new portal," it goes through Agent 1's registry first.

**Interface out:** rows in `raw_documents`, files on disk. Agent 2 reads from here and nowhere else.

---

## Agent 2 — The Refinery (Extraction & Normalization Agent)

**Owns synopsis phases:** 3 (PDF Parsing & OCR), 4 (Schema Normalisation & Data Processing)

**Mission:** Turn heterogeneous raw files into one consistent structured schema.

**Responsibilities:**
- For each `raw_documents` row, detect whether the PDF is text-based or scanned.
- Text-based → extract with `pdfplumber`/`PyPDF2`. Scanned → OCR with `pytesseract`/Tesseract.
- Extract the core fields: 15-minute timestamp, region/state, plant ID, curtailed quantum (MW/MWh), dispatcher remark (free text).
- Normalize: consistent timestamp/timezone format, standardized state/plant identifiers, consistent units.
- Validate and deduplicate before writing to PostgreSQL.
- Flag unparseable documents as `format_unrecognized` for manual review rather than silently dropping data.

**Primary tools:** `pdfplumber`, `PyPDF2`, `pytesseract`, `pandas`, `NumPy`, `SQLAlchemy`.

**Interface out:** rows in `curtailment_events` (structured, normalized, but not yet classified or validated).

---

## Agent 3 — The Analyst (Classification & Cross-Validation Agent)

**Owns synopsis phases:** 5 (NLP Cause Categorisation), 6 (Cross-Validation Logic)

**Mission:** Answer the two hardest questions in the project — *why* was power curtailed, and *is the reported number even real?*

**Responsibilities:**
- Clean and vectorize dispatcher remarks with TF-IDF.
- Classify each remark into standardized causes (Grid Security, High Frequency, Commercial/Discom Request, etc.) using Logistic Regression / SVM.
- Attach a confidence score to each prediction; low-confidence predictions are flagged `needs_review` (see `Brain.md` Rule 3).
- Pull independent schedule-vs-actual generation deviation data from RLDC scheduling portals.
- Match curtailment events to deviation data by timestamp + generating entity.
- Compute `ΔG = Scheduled Generation − Actual Generation` and compare against the reported curtailment quantum to flag whether a "backing-down instruction" corresponds to a real physical reduction.

**Primary tools:** `scikit-learn` (TF-IDF, LogisticRegression/SVC), `pandas`, `NumPy`, `Pydantic` for validating cross-checked records.

**Also owns:** the labeled-dataset bootstrapping work — since no pre-labeled "curtailment cause" dataset exists publicly, this agent's early work includes manually labeling a seed set of ~200–300 dispatcher remarks to train the first classifier version. This is legitimate, demonstrable early progress.

**Interface out:** rows in `curtailment_events` updated with `predicted_cause`, `confidence_score`, `deviation_mw`, `validation_status`.

---

## Agent 4 — The Warden (Compliance & API Agent)

**Owns synopsis phases:** part of 6 (Regulatory Compliance Audit), 7 (API + Dashboard serving layer)

**Mission:** Turn validated data into something regulators, researchers, and the dashboard can actually consume — and hold the system itself accountable to disclosure norms.

**Responsibilities:**
- Compute publication-delay and completeness metrics per portal/region (did SLDC X publish on time? are all required fields present?).
- Produce a **Regulatory Compliance Scorecard**, referencing CERC/IEGC disclosure clauses as the rule set.
- Build and maintain the FastAPI REST layer: endpoints to query curtailment events by date/state/cause, endpoints to fetch compliance scores, CSV export endpoint for open distribution.
- Own API data validation (`Pydantic` schemas) and API-level access patterns the Streamlit dashboard consumes.

**Primary tools:** `FastAPI`, `Pydantic`, `SQLAlchemy`, `pandas` (for CSV export).

**Interface out:** REST API (`/events`, `/compliance`, `/export`) — this is the only interface the dashboard (or any external consumer) talks to. No agent talks to the database directly except through this layer once the system is in "serving" mode.

---

## How the 4 map to your group of 4

| Agent | Suggested owner focus | Good fit if you enjoy... |
|---|---|---|
| 1 — Scout | Web scraping, scheduling, infra reliability | Finding data, dealing with flaky external systems |
| 2 — Refinery | Parsing, OCR, data cleaning | Pandas, regex, "make messy things tidy" |
| 3 — Analyst | NLP, statistics, data science | Scikit-learn, feature engineering, model evaluation |
| 4 — Warden | Backend APIs, dashboards | FastAPI, Streamlit, product-facing work |

This isn't a rigid assignment — it's a starting proposal for your group to divide the FF180 workload so each member can show independent, demonstrable progress to Dr. Kunekar without blocking on each other.
