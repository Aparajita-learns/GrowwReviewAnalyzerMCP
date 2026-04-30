# Weekly Product Review Pulse — Edge Cases & Mitigations

This document tracks potential failure modes, data anomalies, and technical constraints identified during the design of the Review Analyzer agent.

## 1. Data Ingestion Edge Cases

| Edge Case | Impact | Mitigation |
| :--- | :--- | :--- |
| **Zero Reviews Found** | Orchestrator fails or generates empty report. | Check count after ingestion; if 0, log "No new reviews" and skip clustering/delivery. |
| **Review Window Shift** | Missing reviews if run late; overlapping reviews. | Use ISO weeks and specific timestamps to fetch data; store `last_fetched_id` in SQLite. |
| **Scraper Blocked** | Google Play ingestion fails. | Implement rotating user agents or retry logic with exponential backoff. |
| **Extreme Review Volume** | 1000+ reviews in a week; token limit exceeded. | Sample the top 500 reviews by relevance/date or use a multi-stage summarization approach. |

## 2. Processing & LLM Edge Cases

| Edge Case | Impact | Mitigation |
| :--- | :--- | :--- |
| **No Dense Clusters** | HDBSCAN labels all reviews as noise (-1). | Fallback to a simpler K-Means clustering or a general LLM summary of all reviews. |
| **Hallucinated Quotes** | LLM generates "believable" but non-existent quotes. | **Grounding Check:** Post-process quotes to ensure they exist verbatim in the source review text. |
| **PII Leakage** | Sensitive data (phone/email) makes it into the Doc. | Double-layer scrubbing: Regex filter + LLM-based entity detection during preprocessing. |
| **Ambiguous Themes** | Multiple clusters represent the same issue (e.g., "Slow" and "Lag"). | Use the LLM to consolidate similar themes during the Refinement phase. |

## 3. MCP & Delivery Edge Cases

| Edge Case | Impact | Mitigation |
| :--- | :--- | :--- |
| **MCP Server Offline** | Report generated but not delivered. | Implement a `PENDING` state in SQLite; retry delivery on the next run or via CLI. |
| **Doc Access Revoked** | `google-docs-mcp` returns 403. | Log error and alert via CLI; check OAuth status in MCP server config. |
| **Duplicate Runs** | Multiple Doc sections for the same week. | **Idempotency:** Check SQLite for `(product_id, iso_week)` before starting the Delivery phase. |
| **Broken Header Links** | Gmail teaser link doesn't jump to the right Doc section. | Use named anchors or specific heading IDs if supported by the MCP server/Docs API. |

## 4. Operational Edge Cases

| Edge Case | Impact | Mitigation |
| :--- | :--- | :--- |
| **Cost Overrun** | High embedding/LLM usage costs. | Monitor token usage per run; set strict limits in config; use smaller models (e.g., GPT-4o-mini) where possible. |
| **Stale Reports** | Stakeholders see old data as "new". | Ensure the header clearly states the "Week of" and "Data Window" (e.g., Apr 24 - Apr 30). |
