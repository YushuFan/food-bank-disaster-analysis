# Food-bank portfolio release checklist

**Status: ready to publish — v1, 2026-10-11.** Completion means the finished repository and recruiting materials are available and verified. Actual GitHub publication is a subsequent distribution step.

- [x] Clear question, audience, supported result, and prominent visual: [README](README.md).
- [x] Finished visual report with context, investigation, conclusion, and limits: [interactive report](reports/report.html), [readable findings](reports/FINDINGS.md), and [weekly figure](reports/figures/weekly_orders.png).
- [x] Python + SQL reproduce the analysis without R or local Desktop dependencies: [entry point](scripts/reproduce.py), [order SQL](sql/orders.sql), [weekly SQL](sql/weekly.sql).
- [x] Sources, access, grain, keys, dates, units, and exclusions are documented: [data dictionary](data/README.md), [sources](docs/SOURCES.md).
- [x] Metrics, joins, missingness, and anomalies are validated: [audit](data/public/audit.json), [metric tests](tests/test_metrics.py), [ingestion test](tests/test_ingest.py).
- [x] Comparison and uncertainty support the actual claims: [analysis specification](docs/ANALYSIS_PLAN.md), [all model results](reports/results.json). No forecasting or causal claim is made.
- [x] Recommendation states a concrete decision implication and evidence limits: [findings](reports/FINDINGS.md).
- [x] Pinned dependencies, execution instructions, and required aggregate data are included; clean-copy reproduction passed: [verification record](docs/VERIFICATION.md).
- [x] All 24 tests pass, reported values reconcile, and final figures and desktop report were inspected: [verification record](docs/VERIFICATION.md).
- [x] Original R authorship, collaborative context, and Codex-assisted extensions are distinguished: [contribution](docs/SOURCES.md).
- [x] Project card, résumé bullet, pitch, technical walkthrough, behavioral examples, and role emphasis are complete: [recruiting materials](docs/RECRUITING.md).
- [x] Publication files, links, and reuse boundaries are reviewed; no essential placeholders or local source dependencies remain: [packaging script](scripts/package_release.py), [distribution instructions](docs/PUBLISHING.md), and release `MANIFEST.json`.

Verification was performed by Codex, not an independent human reviewer. The raw-source audit cannot be rerun without the original workbook; the included real aggregate data reproduce the complete downstream study. See the verification record for environment and presentation-review limits.
