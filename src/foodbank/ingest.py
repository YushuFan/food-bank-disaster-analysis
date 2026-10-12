"""Stream selected XLSX fields into a local SQLite database without changing inputs.

The source workbook is nearly 1 GB uncompressed. Streaming avoids loading its
full document-line sheet into memory. User tables and contact fields are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import sqlite3
import zipfile

from lxml import etree

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
TABLES = {
    "headers": ("AE - DocumentHeader", ["DOCUMENTID", "SOURCEORG", "STATUS", "CREATEDDATE", "EXPIRYDATE", "MODIFIEDDATE", "WAREHOUSEID", "DOMAINID", "DOMAINNAME", "ARCHIVEDDATE", "ISARCHIVED", "DOCTYPE"]),
    "lines": ("AE - DocumentLine", ["HEADERID", "LINEITEMNUMBER", "ITEMCODE", "DESTINATIONORG", "DONATEDQUANTITY", "STATUS", "ACCEPTEDQUANTITY", "ACCEPTEDDATE", "RECEIPTEDQUANTITY", "RECEIPTEDDATE", "RPROP1"]),
    "organizations": ("RW_ORG", ["ORG_ID", "STATUS_FLAG", "COUNTRY", "ORG_TYPE", "CUSTOM_TYPE", "DOMAIN"]),
}


def clear_element(element):
    element.clear()
    while element.getprevious() is not None:
        del element.getparent()[0]


def sheet_rows(archive, sheet_name):
    """Yield sparse Excel rows keyed by column letters (shared/inline/numeric)."""
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        with archive.open("xl/sharedStrings.xml") as stream:
            for _, element in etree.iterparse(stream, events=("end",), tag=NS + "si"):
                strings.append("".join(element.itertext()))
                clear_element(element)
    workbook = etree.fromstring(archive.read("xl/workbook.xml"))
    relationships = etree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {r.get("Id"): r.get("Target") for r in relationships}
    sheets = {s.get("name"): s.get(REL + "id") for s in workbook.find(NS + "sheets")}
    target = targets[sheets[sheet_name]]
    target = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
    with archive.open(target) as stream:
        for _, element in etree.iterparse(stream, events=("end",), tag=NS + "row"):
            row = {}
            for cell in element:
                if cell.tag != NS + "c":
                    continue
                column = "".join(c for c in cell.get("r", "") if c.isalpha())
                value = cell.findtext(NS + "v")
                if cell.get("t") == "s" and value is not None:
                    value = strings[int(value)]
                elif cell.get("t") == "inlineStr":
                    value = "".join(cell.find(NS + "is").itertext())
                if value is not None:
                    value = value.strip() or None
                row[column] = value
            yield row
            clear_element(element)


def ingest(workbook: Path, database: Path):
    if database.exists():
        raise FileExistsError(f"Refusing to overwrite existing database: {database}")
    database.parent.mkdir(parents=True, exist_ok=True)
    with workbook.open("rb") as stream:
        source_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    manifest = {"source_filename": workbook.name, "size_bytes": workbook.stat().st_size,
                "sha256": source_hash, "tables": {}}
    connection = sqlite3.connect(database)
    try:
        with zipfile.ZipFile(workbook) as archive:
            for table, (sheet, wanted) in TABLES.items():
                rows = sheet_rows(archive, sheet)
                header = next(rows)
                columns = {name: col for col, name in header.items() if name}
                missing = set(wanted) - set(columns)
                if missing:
                    raise ValueError(f"Missing required columns in {sheet}: {missing}")
                connection.execute(f'CREATE TABLE "{table}" (' + ",".join(f'"{c.lower()}" TEXT' for c in wanted) + ")")
                insert = f'INSERT INTO "{table}" VALUES (' + ",".join("?" for _ in wanted) + ")"
                batch, count, blank = [], 0, 0
                for row in rows:
                    values = tuple(row.get(columns[c]) for c in wanted)
                    if all(v is None for v in values):
                        blank += 1
                        continue
                    batch.append(values)
                    count += 1
                    if len(batch) == 10000:
                        connection.executemany(insert, batch)
                        batch.clear()
                        if count % 100000 == 0:
                            print(f"{table}: {count:,} records", flush=True)
                connection.executemany(insert, batch)
                connection.commit()
                manifest["tables"][table] = {"sheet": sheet, "rows": count, "blank_selected_rows": blank, "columns": [c.lower() for c in wanted]}
                print(f"{table}: complete ({count:,} records)", flush=True)
        connection.executescript('CREATE INDEX line_order ON lines(headerid); CREATE INDEX header_order ON headers(documentid); CREATE INDEX org_key ON organizations(org_id);')
        connection.commit()
    finally:
        connection.close()
    database.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    ingest(args.workbook, args.database)


if __name__ == "__main__":
    main()
