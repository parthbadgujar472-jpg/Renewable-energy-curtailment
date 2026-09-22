# PRD.md — Product Requirements Document

**Project:** Renewable Energy Curtailment Analysis and Regulatory Compliance System
**FF No.:** 180 | **Group No.:** 11 | **Guide:** Dr. Pankaj Kunekar | **Dept.:** IT, Semester 03

---

## 1. Problem Statement

Renewable energy curtailment data in India is fragmented across RLDC and SLDC portals, published in inconsistent formats (searchable PDF, scanned PDF, HTML tables, Excel), with unstructured dispatcher remarks that make it hard to determine *why* curtailment happened or *whether it was justified*. There is no open, time-block-level, cross-validated dataset, and no automated way to check whether portals are meeting their disclosure obligations.

## 2. Goals

1. Build an automated pipeline that collects curtailment reports from public RLDC/SLDC/CEA sources daily.
2. Normalize heterogeneous formats into one structured, time-block-level schema.
3. Classify unstructured dispatcher remarks into standardized cause categories (technical vs. commercial/economic) using NLP.
4. Cross-validate reported curtailment events against independent schedule-vs-actual generation data.
5. Score portals/regions on regulatory disclosure compliance (timeliness, completeness).
6. Expose the resulting dataset via a public REST API, CSV export, and an interactive dashboard.

## 3. Non-Goals (explicitly out of scope)

- Real-time (sub-daily) monitoring — reports are published once/day; this is a batch pipeline, not a streaming system.
- Forecasting future curtailment (this is analysis of what happened, not prediction).
- Controlling or interfacing with actual grid hardware/SCADA systems — this is a read-only analytics layer.
- Covering non-Indian grids — scope is India's RLDC/SLDC structure specifically.

## 4. Target Users

| User | What they need from this system |
|---|---|
| Renewable energy researchers | Clean, citable, time-block-level curtailment dataset |
| Renewable generators (developers) | Evidence of whether their curtailment was compensable (non-grid-security cause) |
| Policymakers / regulators (CERC, SERC) | Compliance visibility across regions without manual report review |
| Academic reviewers (your guide, evaluators) | A demonstrably working, well-architected system with traceable data provenance |

## 5. Functional Requirements

**FR1.** System shall scrape and archive raw curtailment/generation reports from at least 2–3 pilot RLDC/SLDC/CEA sources on a daily schedule.
**FR2.** System shall extract structured fields (timestamp, region, plant, curtailed MW/MWh, remark) from both text-based and scanned PDFs.
**FR3.** System shall normalize extracted data into a single PostgreSQL schema regardless of source format.
**FR4.** System shall classify dispatcher remarks into a fixed taxonomy of curtailment causes with an attached confidence score.
**FR5.** System shall compute schedule-vs-actual generation deviation and flag events where reported curtailment does not match physical deviation.
**FR6.** System shall compute a compliance scorecard per region based on publication timeliness and field completeness.
**FR7.** System shall expose all of the above via a documented REST API and support CSV export.
**FR8.** System shall provide an interactive dashboard for filtering by date, state, and cause, and for viewing compliance/cross-validation results.

## 6. Non-Functional Requirements

- **Traceability:** every structured record must be traceable to its original source document (see `Brain.md`, Rule 2).
- **Resilience:** failure of one portal's ingestion must not block ingestion for other portals.
- **Reproducibility:** the pipeline should be re-runnable against historical raw files to regenerate the dataset deterministically.
- **Openness:** the final dataset should be distributable as CSV, not locked behind the dashboard only.
- **Minimum hardware:** runs on a standard laptop (Intel i5 equivalent, 8GB RAM) per the synopsis's stated hardware requirements — no GPU dependency.

## 7. Success Metrics (for evaluation/demo purposes)

| Metric | Target for progress review |
|---|---|
| Regions/portals successfully scraped | ≥ 2 by first progress review |
| Reports parsed into structured schema | ≥ 30 days of data from 1 region |
| NLP classifier accuracy on seed labeled set | Reported honestly, even if modest (e.g. 70–80%) — precision matters more than a high number |
| Cross-validation coverage | % of events with a matched schedule-vs-actual deviation |
| API endpoints live | `/events`, `/compliance` minimum |
| Dashboard | Filterable by date/state/cause, showing at least one full pipeline run's output |

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Portal formats change without notice | Agent 1's format-detection step + `format_unrecognized` flagging (not silent failure) |
| Scanned PDFs give poor OCR quality | Fall back to manual-review queue rather than bad auto-extraction |
| No labeled data for NLP classifier | Manually label a seed set (~200–300 remarks) early — see `Agent.md`, Agent 3 |
| Schedule-vs-actual data harder to access than curtailment data itself | Start cross-validation on 1 region where both are available before generalizing |
| Scope creep (trying to cover all 5 regions at once) | Pilot with 1–2 regions first, expand only after pipeline is proven end-to-end |
