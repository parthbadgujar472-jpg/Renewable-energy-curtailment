# Decisions.md — Architecture Decision Records (ADRs)

Lightweight ADR log. Each entry: the decision, why, and what we gave up. Add new entries at the top as the project evolves — this file is a living record of *why the system looks the way it does*, which is exactly what a guide/evaluator will probe in a progress review.

---

## ADR-007: Minimal API Serving Layer
**Decision:** The API layer (`api/main.py`) is intentionally minimal — containing exactly 3 endpoints (`/events`, `/compliance`, `/export/csv`), and zero business logic. All data transformation, filtering, and aggregation logic is strictly delegated to the respective agent modules (`agents/analyst`, `agents/warden`, etc.).
**Why:** The API layer was growing disproportionately large with embedded filtering, data transformation, and pagination logic, which diluted the focus on the core contribution (the 4-agent data pipeline). By pushing logic down, the `api/` directory remains a thin wrapper, and the project's core intelligence is visibly concentrated in the `agents/` modules.
**Trade-off:** None significant. It properly enforces the architectural boundaries defined in `Agent.md`.

## ADR-006: Compliance scores are derived and never mutate source data
**Decision:** `compliance_scores` is a separate table computed from `curtailment_events` and `raw_documents` timestamps; Agent 4 never writes back into `curtailment_events`.
**Why:** Keeps the audit trail defensible — if the compliance score is ever disputed by a regulator or generator, the underlying event data is untouched and independently verifiable.
**Trade-off:** Slightly more joins at query time in the API layer; acceptable given the dataset size (daily batch, not high-frequency).

## ADR-005: Low-confidence NLP predictions are flagged, not hidden
**Decision:** Every classified dispatcher remark carries a `confidence_score`; predictions below 0.6 are marked `needs_review` rather than presented as equally certain to high-confidence ones.
**Why:** Dispatcher remarks are short, inconsistent free text. A classifier trained on a small seed-labeled set (see `Agent.md`, Agent 3) will not be uniformly reliable, and hiding that uncertainty would misrepresent the system's actual capability — especially important since this feeds into a *regulatory compliance* tool.
**Trade-off:** Dashboard must design for "confidence" as a first-class concept, not an afterthought.

## ADR-004: TF-IDF + Logistic Regression/SVM over a deep-learning classifier
**Decision:** Use `scikit-learn`'s TF-IDF vectorization with Logistic Regression or SVM for cause classification, not a transformer-based model.
**Why:** (1) No large labeled dataset of Indian dispatcher remarks exists — a seed set of a few hundred examples suits classical ML far better than a model that needs thousands of examples to avoid overfitting. (2) Runs on CPU, matching the stated hardware constraint (8GB RAM, no GPU). (3) Interpretable — for a regulatory-compliance context, being able to inspect which words drove a classification matters more than squeezing out a few extra points of accuracy.
**Trade-off:** Ceiling on classification accuracy is lower than a fine-tuned transformer could theoretically achieve. Acceptable given data availability and interpretability requirements; can be revisited if the labeled dataset grows substantially.

## ADR-003: PostgreSQL over a NoSQL/document store
**Decision:** Structured events live in PostgreSQL via SQLAlchemy.
**Why:** The data is inherently relational (event → source document → region → compliance score), and the dashboard/API need SQL-style aggregation (group by state/cause/month) which relational databases do naturally and document stores make awkward.
**Trade-off:** Schema changes require migrations; considered acceptable since the schema (timestamp, region, plant, quantum, remark) is stable and well-defined by the domain, not expected to churn.

## ADR-002: Four independent agents with database-mediated handoffs, not a single monolithic script
**Decision:** Split the pipeline into four agents (Scout, Refinery, Analyst, Warden — see `Agent.md`) that communicate only by reading/writing shared database tables, not via direct function calls or a shared in-memory state.
**Why:** (1) Matches the group's structure — four members can build and test their agent independently. (2) Matches the project's own risk profile: portal formats will change, OCR will sometimes fail, NLP confidence will vary — a single tightly-coupled script would mean one failure blocks everything, whereas independent agents let the pipeline degrade gracefully per the rules in `Brain.md`. (3) Makes partial progress demonstrable — e.g., showing a working Agent 1 + Agent 2 even before Agent 3's classifier is polished.
**Trade-off:** Slightly more engineering overhead (defined table schemas as contracts, no shared code shortcuts) versus a quick single-script prototype. Justified by the team size and the semester-long timeline.

## ADR-001: Batch/daily scheduling over real-time polling
**Decision:** APScheduler triggers ingestion once (or twice) daily, not a continuously running scraper/stream processor.
**Why:** RLDC/SLDC/CEA portals publish reports once (occasionally twice) per day — there is no real-time feed to poll. Building streaming infrastructure for daily-cadence data would be over-engineering relative to the actual problem.
**Trade-off:** None significant — this matches the actual publication cadence of the source data, so there's no capability being sacrificed.

---

## Open decisions (not yet finalized — flag to guide if relevant)

- **Pilot region selection:** which 1–2 regions (e.g., Southern Region via SRLDC, given the existing APTEL/Tamil Nadu precedent) to build and validate the pipeline against first, before generalizing to all five regions.
- **OCR engine choice for low-quality scans:** whether Tesseract alone is sufficient or a cloud OCR fallback is needed for poor-quality scanned reports — to be decided after testing on real sample documents.
- **Compliance rule set granularity:** how finely to encode CERC/IEGC disclosure clauses into the scorecard (binary pass/fail per rule vs. a weighted score) — deferred until the Warden agent's design phase.
