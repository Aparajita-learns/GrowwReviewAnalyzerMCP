# Weekly Product Review Pulse — Evaluation Plan

This plan defines the metrics and processes used to evaluate the quality, reliability, and business value of the Review Analyzer agent.

## 1. Quality Metrics (LLM & Clustering)

| Metric | Definition | Target |
| :--- | :--- | :--- |
| **Quote Veracity** | % of quotes that exist verbatim in the source reviews. | 100% |
| **Theme Coherence** | Human rating (1-5) of how well the themes match the underlying reviews. | > 4.0 |
| **Actionability** | % of "Action Ideas" deemed useful by Product Managers. | > 70% |
| **Clustering Coverage** | % of reviews successfully assigned to a cluster (excluding noise). | > 60% |

## 2. System Performance Metrics

| Metric | Definition | Target |
| :--- | :--- | :--- |
| **End-to-End Latency** | Time from CLI trigger to Gmail delivery. | < 5 mins |
| **Cost per Run** | Total API cost (OpenAI/Gemini) per product/week. | < $0.50 |
| **Delivery Success** | % of runs that successfully update Docs and send Gmail without manual retry. | > 95% |
| **Idempotency Accuracy** | 0 duplicate Doc sections or duplicate emails for the same week. | 100% |

## 3. Evaluation Process

### A. Automated Checks (CI/CD)
- **Unit Tests:** Verify ingestion modules, PII scrubber, and idempotency logic.
- **Grounding Test:** A script that automatically cross-references generated quotes against the raw JSON review data.
- **Schema Validation:** Ensure the output formatted for Google Docs matches the expected `batchUpdate` structure.

### B. Periodic Human Review
- **Weekly Pulse Audit:** For the first 4 weeks, a Product Manager will review the generated Doc section and Gmail teaser for accuracy and tone.
- **Feedback Collection:** Stakeholders can reply to the teaser email with feedback, which is logged to improve the LLM prompts.

### C. Benchmarking
- Compare the AI-generated "Top Themes" against a manually labeled dataset of 100 reviews once every quarter to monitor for "model drift" or quality degradation.

## 4. Success Criteria for Production
1.  System runs autonomously for 2 weeks across all 5 products without a crash.
2.  Stakeholders from at least 3 departments (Product, Support, Leadership) confirm they have used the Doc to inform a decision.
3.  Zero PII leaks recorded in the public-facing Google Docs.
