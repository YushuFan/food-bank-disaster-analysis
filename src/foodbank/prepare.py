"""Validate source tables, run SQL metrics, and export publication-safe aggregates."""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def iso_date(value):
    if value is None or str(value).strip() == "":
        return None
    value = str(value).strip()
    if len(value) != 8 or not value.isdigit():
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def safe_number(value):
    if value is None:
        return None
    try:
        result = float(str(value).replace(",", "").replace("$", ""))
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def scalar(c, query):
    return c.execute(query).fetchone()[0]


def validate(c):
    counts = {
        "headers": scalar(c, "SELECT COUNT(*) FROM headers"),
        "lines": scalar(c, "SELECT COUNT(*) FROM lines"),
        "organizations": scalar(c, "SELECT COUNT(*) FROM organizations"),
        "duplicate_header_ids": scalar(c, "SELECT COUNT(*)-COUNT(DISTINCT documentid) FROM headers"),
        "duplicate_line_keys": scalar(c, "SELECT COUNT(*) FROM (SELECT headerid,lineitemnumber,COUNT(*) n FROM lines GROUP BY 1,2 HAVING n>1)"),
        "orphan_lines": scalar(c, "SELECT COUNT(*) FROM lines l LEFT JOIN headers h ON l.headerid=h.documentid WHERE h.documentid IS NULL"),
        "inconsistent_order_dates": scalar(c, "SELECT COUNT(*) FROM (SELECT headerid FROM lines GROUP BY 1 HAVING COUNT(DISTINCT accepteddate)>1)"),
        "missing_acceptance_lines": scalar(c, "SELECT COUNT(*) FROM lines WHERE accepteddate IS NULL"),
        "invalid_acceptance_lines": scalar(c, "SELECT COUNT(*) FROM lines WHERE accepteddate IS NOT NULL AND ISO_DATE(accepteddate) IS NULL"),
        "receipt_date_present_lines": scalar(c, "SELECT COUNT(*) FROM lines WHERE receipteddate IS NOT NULL"),
        "positive_quantity_lines": scalar(c, "SELECT COUNT(*) FROM lines WHERE SAFE_NUMBER(acceptedquantity)>0"),
        "zero_quantity_lines_with_date": scalar(c, "SELECT COUNT(*) FROM lines WHERE ISO_DATE(accepteddate) IS NOT NULL AND SAFE_NUMBER(acceptedquantity)=0"),
    }
    for key in ["duplicate_header_ids", "duplicate_line_keys", "orphan_lines", "inconsistent_order_dates", "invalid_acceptance_lines"]:
        if counts[key]:
            raise ValueError(f"Validation failed: {key}={counts[key]}. Resolve before aggregation.")
    return counts


def prepare(database: Path, events: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(database)
    c.create_function("ISO_DATE", 1, iso_date, deterministic=True)
    c.create_function("SAFE_NUMBER", 1, safe_number, deterministic=True)
    audit = validate(c)
    c.executescript((ROOT / "sql/orders.sql").read_text())
    weekly = pd.read_sql_query((ROOT / "sql/weekly.sql").read_text(), c)
    # No source identifiers or organization-level records are exported.
    weekly.to_csv(out / "weekly_orders.csv", index=False)
    audit.update({
        "orders_with_lines": scalar(c, "SELECT COUNT(*) FROM analytical_orders"),
        "orders_without_acceptance_date": scalar(c, "SELECT COUNT(*) FROM analytical_orders WHERE accepted_date IS NULL"),
        "orders_with_positive_quantity": scalar(c, "SELECT COUNT(*) FROM analytical_orders WHERE positive_lines>0"),
        "orders_with_acceptance_before_creation": scalar(c, "SELECT COUNT(*) FROM analytical_orders WHERE date_anomaly=1"),
        "primary_orders_all_years": int(weekly.positive_orders.sum()),
        "acceptance_date_min": scalar(c, "SELECT MIN(accepted_date) FROM analytical_orders"),
        "acceptance_date_max": scalar(c, "SELECT MAX(accepted_date) FROM analytical_orders"),
        "missing_organization_matches": scalar(c, "SELECT COUNT(*) FROM headers h LEFT JOIN organizations o ON h.sourceorg=o.org_id WHERE o.org_id IS NULL"),
        "line_status_counts": dict(c.execute("SELECT COALESCE(status,'MISSING'),COUNT(*) FROM lines GROUP BY 1").fetchall()),
    })
    c.close()
    e = pd.read_csv(events, skiprows=2, dtype=str)
    e = e.rename(columns={"Name":"name", "Disaster":"type", "Begin Date":"start", "End Date":"end"})
    e["start"] = e.start.map(iso_date)
    e["end"] = e.end.map(iso_date)
    if e[["start", "end"]].isna().any().any() or (e.end < e.start).any():
        raise ValueError("Invalid event dates")
    # Exclude monetary damages from the analytical export: geography/measurement
    # do not support treating these regional event costs as local daily severity.
    e = e[["name", "type", "start", "end"]].sort_values(["start", "name"])
    e.to_csv(out / "disaster_events.csv", index=False)
    audit["disaster_events"] = len(e)
    audit["source_workbook"] = json.loads(database.with_suffix(".manifest.json").read_text())
    with events.open("rb") as f:
        audit["source_events_sha256"] = hashlib.file_digest(f,"sha256").hexdigest()
    (out / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({k:v for k,v in audit.items() if k != "source_workbook"},indent=2))
    return weekly, audit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database", type=Path, required=True)
    p.add_argument("--events", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / "data/public")
    a=p.parse_args()
    prepare(a.database,a.events,a.out)


if __name__ == "__main__":
    main()
