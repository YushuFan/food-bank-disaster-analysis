# Data dictionary and reproduction boundary

## Source tables

| Table | Grain and key | Inspected records | Analytical use |
|---|---|---|---|
| AE document header | Order, `DOCUMENTID` | 84,399 | Source organization and creation date |
| AE document line | Order line, `HEADERID` + `LINEITEMNUMBER` | 606,316 | Acceptance date, positive accepted-quantity eligibility |
| RW_ORG | Organization, `ORG_ID` | 1,429 | Validate source-organization linkage; no individual contacts exported |

`ACCEPTEDDATE` is stored as YYYYMMDD. All nonempty values parse as valid dates. Every order's nonempty line acceptance dates agree. `CREATEDDATE` is also parsed strictly. Invalid dates are never silently converted to zero activity. The original ER diagram supports the order-line and organization-header relationships.

`ACCEPTEDQUANTITY` is used only to test whether a line has a strictly positive numeric quantity. Its units are not harmonized across products, so quantities are not summed into a physical volume. `RPROP1` is retained in the private selected-field database for audit but its meaning is insufficiently documented for a transaction-dollar total. Status codes are not decoded without documentation. Every receipt date is absent, and neither acceptance dates nor status codes establish completed delivery.

## Published weekly aggregate

`public/weekly_orders.csv` has one row for each Monday-start week with at least one dated order, over the available source history. There are no order IDs, organization IDs, names, emails, or item-level records.

| Column | Definition |
|---|---|
| week | Monday starting the calendar week containing the acceptance date |
| dated_orders | Distinct orders with a valid recorded acceptance date, regardless of quantity or date anomaly |
| positive_orders | Distinct orders with at least one dated positive-quantity line and no acceptance-before-creation anomaly |
| positive_orders_including_date_anomalies | Same positive-quantity criterion without excluding date anomalies |
| positive_lines | Number of dated positive-quantity lines on orders without date anomalies |
| dated_lines | Number of lines with a valid acceptance date |
| active_organizations | Distinct source-organization IDs among that week's primary orders; an activity measure, not a census of all organizations |
| anomalous_orders | Orders whose acceptance date predates their valid creation date |

Each order contributes once to a weekly count. A weekly organization count must not be summed to claim annual unique organizations. An unrepresented week is unknown, not a zero observation. Modeling reindexes the calendar explicitly.

## Disaster snapshot

`public/disaster_events.csv` contains 72 events from the supplied 2014–2024 Georgia-event CSV: `name`, `type`, `start`, and `end`. Its original header identifies costs in millions of dollars, but costs are excluded from this analysis because regional totals are not a defensible local daily severity measure.

The primary types are Severe Storm, Flooding, Winter Storm, and Tropical Cyclone. Exposure equals any intersection of a Monday–Sunday week with an eligible inclusive event interval. Overlapping events are a union, not duplicated observations. The 14-day sensitivity extends event end dates; it is not a prospective forecast feature.

## Audit manifest

`public/audit.json` records counts, validation checks, selected source columns, and original file SHA-256 hashes. All-year totals and 2014–2023 model totals differ deliberately. The main sample has 55,201 qualifying orders and 58,289 broadly dated orders. One of 521 calendar weeks is unobserved (2022-12-26); it is excluded from models and shown as a gap.

## Optional raw-source rebuild

The bundled aggregate workflow in the README reproduces all published analyses. Rebuilding those aggregates requires the owner's original `AE Data.xlsx` and `events-GA-2014-2024.csv`; the large workbook is not bundled. Obtain those source files from the project owner if access is needed. Their hashes are in the audit manifest.

Run from the project root after installing requirements. Substitute actual source locations:

```bash
PYTHONPATH=src python -m foodbank.ingest --workbook /path/to/AE_Data.xlsx --database .local/source.sqlite
PYTHONPATH=src python -m foodbank.prepare --database .local/source.sqlite --events /path/to/events-GA-2014-2024.csv --out data/public
python scripts/reproduce.py
```

The ingestion command refuses to overwrite an existing database. It never edits the source workbook. The illustrative workbook path may have any filename; source identity is checked through the recorded hash. In PowerShell, set `$env:PYTHONPATH="src"` before running the Python module commands.

The raw-source workflow includes exact key/join/date validation. The aggregate-only workflow can validate aggregate invariants and re-estimate models, but cannot prove the original rows were correctly extracted without the raw workbook. This boundary is intentional and disclosed.
