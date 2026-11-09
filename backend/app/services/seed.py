"""Imports the generated benchmark dataset (dataset/testcases.csv) into the database.

Runs on every start and upserts by ID, so a regenerated dataset is picked up after a
restart. The CSV is produced by dataset/generate.py (DS-06) and is the single source of
truth for seed test cases; the API does not allow changing them.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from sqlmodel import Session

from app.models.error_types import ERROR_TYPES, NO_ERROR, category_of
from app.models.testcase import ExpectedResult, TestCase, TestCaseKind, TestCaseSource

log = logging.getLogger(__name__) #Faults are logged and the program continues afterwards 

MANIFEST_NAME = "testcases.csv"

'''
Converts a CSV line into db fields 
'''
def _row_to_fields(row: dict[str, str]) -> dict:
    error_type = row["error_type"] or NO_ERROR
    if error_type not in ERROR_TYPES:
        raise ValueError(f"unknown error type '{error_type}'")
    return {
        "kind": TestCaseKind(row["kind"]),
        "name": row["name"],
        "description": row["description"],
        "reference_id": row["reference_id"] or None,
        "expected_result": ExpectedResult(row["expected_result"]),
        "error_type": error_type,
        "category": category_of(error_type),
        "is_edge_case": row["is_edge_case"].strip().lower() == "true",
        "source": TestCaseSource.SEED,
        "sha256": row["sha256"],
        "file": row["file"],
        "manipulation": json.loads(row["params"]) if row["params"] else None,
    }

'''
Actual Import of the dataset. Takes a session and the dataset folder and returns the number of imported lines
'''
def seed_dataset(session: Session, dataset_dir: Path) -> int:
    """Upserts all rows of the manifest. Returns the number of imported rows."""
    manifest = dataset_dir / MANIFEST_NAME
    if not manifest.is_file():
        log.warning("No dataset manifest at %s, skipping seed import", manifest)
        return 0

    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    # References first, so test cases always point to an existing row.
    rows.sort(key=lambda r: r["kind"] != TestCaseKind.REFERENCE.value)

    imported = 0
    for row in rows: #loop over all rows
        try:
            fields = _row_to_fields(row)
        except (KeyError, ValueError) as exc:
            log.error("Skipping dataset row %s: %s", row.get("id"), exc)
            continue
        # Upsert-logic (update or insert)
        existing = session.get(TestCase, row["id"])
        if existing is None:
            session.add(TestCase(id=row["id"], **fields))
        elif existing.source == TestCaseSource.SEED:
            existing.sqlmodel_update(fields)
        else:
            log.error("Dataset ID %s collides with an uploaded test case, skipping", row["id"])
            continue
        imported += 1

    # Runs every startup to ensure that newly created get loaded in the db
    session.commit()
    log.info("Imported %d test cases from %s", imported, manifest)
    return imported
