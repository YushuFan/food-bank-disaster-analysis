# Sources, attribution, and reuse notes

## Inputs

- Agency Express source workbook supplied for the AI.Data Lab / TechBridge project. Original filename: `AE Data.xlsx`. Source file hash and table manifest: `../data/public/audit.json`.
- Supplied NOAA NCEI event CSV, `events-GA-2014-2024.csv`. Its header describes weather and climate billion-dollar disasters affecting Georgia, 2014–2024, with costs in millions of dollars. This is a fixed historical snapshot, not a live feed. Original dataset identifier: DOI 10.25921/stkw-7w73. Original export route: https://www.ncei.noaa.gov/access/billions/events/GA/2014-2024 . Access to that historical route may change; the analysis uses the bundled dated-event snapshot.
- Original R analysis authored by Yushu Fan; collaborative project context from the supplied project materials. The rebuild does not distribute interviews, presentation decks, organizational names, personal contacts, or the complete workbook.
- Supplied TechBridge ER diagram confirms line-to-header and header-to-organization relations. The diagram is used as a reference, not copied into the release.

## Method references

- NOAA, *U.S. Billion-Dollar Disasters in Seasonal Context*, April 28, 2020: https://www.ncei.noaa.gov/news/us-billion-dollar-disasters-seasonal-context . State inclusion can reflect participation in a regional event; this supports avoiding an unsupported conversion to pantry-local severity.
- Statsmodels, robust covariance documentation: https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html . The complete-calendar HAC reference is used in the covariance equivalence test. The missing-week extension uses calendar distances and is documented in the code and analysis plan.

## Contribution

Yushu Fan authored the supplied R analyses. The Python + SQL reimplementation, validation tests, statistical review, and report were developed with OpenAI Codex assistance under the owner's direction. The original project involved collaborators; no sole ownership of team presentations or reports is asserted. The owner should review the code and reasoning before presenting the work in interviews.

## Publication and reuse

The owner explicitly confirmed permission to publish the food-bank materials on 2026-10-11. Only aggregate records needed to reproduce the case study are distributed here; source paths and personal identifiers are absent. Publication does not imply partner endorsement.

No repository-wide open-source license is declared. Third-party source material retains its applicable terms. The owner's permission to publish this portfolio is not presented as a blanket grant to redistribute the original partner materials. Package dependencies carry their own licenses.
