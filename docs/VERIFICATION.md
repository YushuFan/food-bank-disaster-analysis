# Verification record

Release: v1, 2026-10-11. Review performed by Codex; no independent human review or stakeholder adoption is claimed.

## Execution

- Created a fresh Python 3.12 virtual environment and installed the pinned dependencies in `requirements.txt`.
- Ran selected-field ingestion and SQL preparation against the supplied original workbook. The audit covers 84,399 headers, 606,316 lines, and 1,429 organizations. Source hashes and validation counts are in [audit.json](../data/public/audit.json).
- Ran `python -m pytest`: **24 tests passed**. Tests cover sparse/shared/inline spreadsheet values, strict dates, numeric eligibility, order versus line counts, duplicate/orphan/date-consistency failures, date anomalies, overlapping events, missing weeks, and calendar-aware HAC covariance.
- Ran `python scripts/reproduce.py` successfully using the bundled public aggregates. All six specifications, findings, figures, and the interactive report were generated.
- Packaged a clean source copy without the original workbook, intermediate database, virtual environment, or development sources. With `PYTHONPATH` unset, ran all 24 tests and reproduction again from that copy using the freshly installed pinned environment. The resulting numerical JSON matched exactly; both generated PNG figures were byte-for-byte identical.

This verifies a clean source copy in the tested macOS/Python environment. A separate operating system or independently provisioned machine was not tested. The source-record audit requires the original workbook; the released aggregates independently reproduce the downstream analysis and presentation.

## Numerical reconciliation

| Check | Verified value |
|---|---|
| Complete study calendar | 521 weeks, 2014-01-06 through 2023-12-25 |
| Observed weeks | 520; week starting 2022-12-26 is unknown |
| Primary qualifying orders | 55,201 |
| Acute-disaster overlap weeks | 70 observed weeks |
| Adjusted modeled contrast | −2.8716% |
| Normal-approximation 95% interval | −13.0040% to +8.4410% |
| Sensitivity results | All six intervals include zero |

Values reconcile with [results.json](../reports/results.json), the report, README, and recruiting narrative. The contrast is on the modeled orders-plus-one scale. No causal effect, completed delivery, operational improvement, or proof of no disaster impact is claimed.

## Presentation review

- Inspected both generated static figures for readable labels, units, uncertainty, and consistency with numerical results.
- Opened the HTML report in a desktop browser and inspected its headline, metric cards, evidence, methods, and limitations.
- Exercised the metric selector and one-year time-range button. Confirmed the metric axis changes and the one-year window stays within the study period after fixing an initial padded-axis issue.
- Removed an irrelevant chart-sharing control. The delivered HTML embeds its chart dependencies and images for local viewing.
- Reviewed the project card, résumé bullet, walkthrough, and behavioral examples against documented work. Interview fluency remains personal preparation, not a tested result.

Mobile layouts and every browser version were not tested.

## Publication boundary

The release script selects explicit code, documentation, aggregate-data, and report paths. The release excludes original records, contact/user tables, source documents, development paths, environments, and intermediate databases. Local Markdown links and file hashes are checked during packaging. `MANIFEST.json` records SHA-256 hashes of the packaged files; it does not hash itself.

The repository is ready for publication. No GitHub upload, hosted deployment, external review, or recruiter outcome has occurred as part of this verification.
