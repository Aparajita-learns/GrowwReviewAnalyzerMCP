# Weekly Product Review Pulse — Implementation Plan

This plan breaks down the development of the Review Analyzer agent into five distinct phases, following the design in [architecture.md](file:///c:/Users/apagupta/OneDrive%20-%20Microsoft/ProductManagementPrep/LIP/GrowwReviewAnalyzerMCP/architecture.md).

## Phase 1: Foundation & Data Ingestion
**Goal:** Build the pipes to fetch and clean raw review data.

- [x] **Project Setup:** Initialize Python/Node.js environment, install dependencies (`mcp`, `pandas`, `sqlite3`).
- [x] **Ingestion Modules:**
    - [x] App Store RSS reader (iTunes Customer Reviews).
    - [x] Google Play scraper (e.g., `google-play-scraper` library).
- [x] **PII Scrubber:** Implement regex and basic NLP filters to mask sensitive user data.
- [x] **Local Storage:** Setup SQLite schema for `runs`, `reviews_raw`, and `deliveries`.

## Phase 2: Processing & Clustering Engine
**Goal:** Transform raw text into structured themes and insights.

- [x] **Embeddings Pipeline:** Integrate with OpenAI/Gemini to generate vectors for cleaned reviews.
- [x] **Clustering Implementation:**
    - [x] UMAP for dimensionality reduction.
    - [x] HDBSCAN for identifying review clusters.
- [x] **LLM Refinement Layer:**
    - [x] Theme naming based on cluster samples.
    - [x] Quote selection and "grounding" check (ensuring quotes exist verbatim).
    - [x] Actionable insights generation.

## Phase 3: LLM Summarization
**Goal:** Convert numeric clusters into named themes, verbatim quotes, and action ideas with strong grounding guarantees.

- [x] **Data Structures:** Implement Pydantic models for `Theme`, `Quote`, `ActionIdea`, and `PulseSummary`.
- [x] **LLM Client Wrapper:** Create a robust wrapper with:
    - [x] Retries, timeouts, and error handling.
    - [x] Token/cost accounting (persisted to SQLite `runs` table).
    - [x] Per-run cost hard cap.
- [x] **Summarization Logic (`agent/summarization.py`):**
    - [x] `label_theme`: Name clusters based on keyphrases and samples.
    - [x] `select_quotes`: Implement verbatim validator (ensure quotes exist in raw text).
    - [x] `generate_action_ideas`: Propose product improvements.
    - [x] `summarize_pulse`: Assembly and ranking of top themes.
- [x] **PII Re-scrub:** Secondary cleaning before LLM calls.
- [x] **CLI Integration:** `pulse summarize --run <id>` command.

## Phase 4: Report & Email Rendering
**Goal:** Deterministic conversion of `PulseSummary` into Google Docs batchUpdate requests and HTML email.

- [x] **Docs Renderer (`agent/renderer/docs_tree.py`):**
    - [x] Convert `PulseSummary` to `batchUpdate` request tree.
    - [x] Implement stable anchor string `pulse-{product}-{iso_week}`.
    - [x] Schema validation for the request tree.
- [x] **Email Renderer (`agent/renderer/email_html.py`):**
    - [x] Jinja2 templates for HTML and plain-text.
    - [x] Dynamic subject line: `[Weekly Pulse] {Product} — {ISO week} — {Top theme}`.
    - [x] Deep-link placeholder `{DOC_DEEP_LINK}`.

## Phase 5: MCP Integration & CLI Orchestration
**Goal:** Finalize delivery via MCP and provide the master end-to-end command.

- [x] **MCP Host Setup:** Connect to `google-docs-mcp` and `gmail-mcp` servers.
- [x] **End-to-End Orchestrator:**
    - [x] Link Ingest -> Process -> Summarize -> Render -> Deliver.
    - [x] Implement the `run` and `backfill` CLI commands.
- [x] **Idempotency & Auditing:** Record delivery identifiers and metadata in SQLite.
- [x] **Automation:** GitHub Actions / Cron configuration.
