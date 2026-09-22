# Brain.md — Core System Intelligence & Orchestration Logic

## Purpose of this document
This is the "how the system thinks" document. `Architecture.md` describes the components; `Agent.md` describes who does what. This file describes the **orchestration logic that ties the four agents into one coherent pipeline** — the decision rules, state machine, and control flow that make the system behave as a single product rather than four disconnected scripts.

---

## 1. The Core Loop

The system runs on a **daily event-driven loop**, triggered by APScheduler, not a continuous stream. Renewable curtailment reports are published once (sometimes twice) a day by RLDC/SLDC portals, so real-time polling is wasted effort — the Brain's first decision is *when to wake up*.

```
[Scheduler tick, e.g. 08:00 IST daily]
        │
        ▼
┌───────────────────┐
│  Agent 1: Scout    │  "Is there anything new to fetch today?"
└─────────┬──────────┘
          │ raw files (PDF/HTML/XLSX) + manifest
          ▼
┌───────────────────┐
│  Agent 2: Refinery │  "Can I turn this into a clean row?"
└─────────┬──────────┘
          │ structured records (validated, deduped)
          ▼
┌───────────────────┐
│  Agent 3: Analyst  │  "Why was this curtailed, and is the number real?"
└─────────┬──────────┘
          │ classified + cross-validated events
          ▼
┌───────────────────┐
│  Agent 4: Warden   │  "Was this reported on time and completely?"
└─────────┬──────────┘
          │ compliance scorecard + API-ready dataset
          ▼
   [PostgreSQL] → [FastAPI] → [Streamlit Dashboard]
```

Each arrow is a **handoff contract**, not a function call — each agent writes its output to a defined table/queue and the next agent picks it up independently. This is deliberate: if Agent 3 (NLP) fails or is mid-development, Agents 1 and 2 keep working and data keeps accumulating. No single agent blocks the pipeline.

---

## 2. Decision Rules the Brain Enforces

These are the cross-cutting rules that don't belong to any one agent, but govern how they interact:

### Rule 1 — Never trust a single source blindly
Every curtailment event must eventually carry two independent signals before it's considered "confirmed": (a) the *reported* value from the RLDC/SLDC dispatcher log, and (b) the *derived* value from schedule-vs-actual generation deviation (ΔG). Until both exist, a record's `validation_status` is `pending`, not `confirmed`. This directly operationalizes the project's Gap #4 (lack of event-level cross-validation).

### Rule 2 — Every record is traceable to its raw source
No structured row exists without a `source_document_id` pointing back to the original PDF/HTML/XLSX file as ingested by Agent 1. This is non-negotiable for a regulatory-compliance tool — if a stakeholder disputes a number, the system must be able to show the original document it came from.

### Rule 3 — Classification confidence gates automation
The NLP cause-classifier (Agent 3) attaches a confidence score to every prediction. Below a threshold (default 0.6), the record is flagged `needs_review` instead of being silently auto-labeled. This avoids the pipeline overclaiming precision it doesn't have — important because dispatcher remarks are short, inconsistent free text.

### Rule 4 — Compliance scoring never mutates source data
Agent 4's compliance scorecard is a *derived view*, computed from publication timestamps and completeness checks. It never edits the underlying curtailment records — it only annotates them. This keeps the audit trail clean and defensible.

### Rule 5 — Degrade gracefully per portal, not globally
If one RLDC/SLDC portal changes its report format or goes down, only that region's ingestion pauses (logged, retried, alerted). The rest of the pipeline continues for other regions. The system's unit of failure is "one portal on one day," never "the whole system."

---

## 3. State Model

Every curtailment event moves through a small, explicit state machine — this is what the dashboard ultimately visualizes and what the API exposes as `status`:

```
raw_ingested → extracted → normalized → classified → cross_validated → compliance_scored
                    │            │            │              │
                    └── error states at each stage: needs_ocr_retry,
                        needs_review, schedule_data_missing, format_unrecognized
```

This state model is the single most important artifact to show your guide early — it demonstrates the pipeline is a real system with defined checkpoints, not a black box.

---

## 4. Why "Brain" is separate from "Agents"

`Agent.md` defines each agent as if it could be built and tested in isolation (and it should be — this is good engineering practice for a 4-person team, since each member can own one agent). `Brain.md` exists so that **no one person has to hold the full cross-agent logic in their head** — it's written down once, here, and referenced by whoever is wiring the agents together (likely whoever owns the orchestration/scheduling layer).

This separation also gives you a clean story for progress reviews: *"Agent 1 is fully working end-to-end, Agent 2 is in progress, and here is the documented contract for how they'll connect"* — which is a legitimate, demonstrable form of progress even before every agent is finished.
