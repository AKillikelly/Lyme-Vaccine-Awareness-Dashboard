#!/usr/bin/env python3
"""Validate the static Lyme vaccine awareness dashboard before GitHub Pages deploy.

The dashboard intentionally uses a small, transparent JSON data model. This
script fails fast when required fields are missing, IDs are duplicated, matrix
terms drift, or local files referenced by the site are absent.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "data" / "lyme_vaccine_map_data_v0_1.json"
PIPELINE_CSV = ROOT / "data" / "lyme_vaccine_pipeline_seed_v0_1.csv"
EVIDENCE_CSV = ROOT / "data" / "lyme_vaccine_evidence_records_v0_1.csv"
INDEX_HTML = ROOT / "index.html"
SEED_IMAGE = ROOT / "assets" / "funnelgram_seed.png"

REQUIRED_TOP_LEVEL_KEYS = {
    "metadata",
    "pipeline_stages",
    "candidates",
    "rows",
    "columns",
    "records",
    "gaps",
    "method_sources",
}

REQUIRED_CANDIDATE_FIELDS = {
    "id",
    "candidate",
    "developer",
    "platform",
    "population",
    "route",
    "current_stage_id",
    "current_stage",
    "stage_order",
    "dashboard_status_text",
    "source_confidence",
    "source_url",
    "source_date",
    "map_record_updated",
}

REQUIRED_RECORD_FIELDS = {
    "id",
    "candidate_id",
    "candidate",
    "developer",
    "title",
    "citation",
    "year",
    "matrix_row",
    "matrix_column",
    "phase",
    "key_finding",
    "evidence_signal",
    "actionability",
    "verification_status",
    "source_url",
    "evidence_update_date",
    "map_record_updated",
}

REQUIRED_HTML_MARKERS = [
    "funnelGrid",
    "candidateTable",
    "matrix",
    "records",
    "gaps",
    "filters",
    "copyBtn",
    "data/lyme_vaccine_map_data_v0_1.json",
]

ALLOWED_SOURCE_PREFIXES = (
    "https://",
    "http://",
    "assets/",
    "data/",
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"Missing JSON data file: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")


def require_fields(item: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(field for field in required if field not in item or item[field] in (None, ""))
    if missing:
        fail(f"{label} is missing required fields: {', '.join(missing)}")


def assert_unique(items: list[dict[str, Any]], field: str, label: str) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        value = str(item.get(field, "")).strip()
        if not value:
            fail(f"{label} contains a blank {field}")
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        fail(f"{label} contains duplicate {field} values: {', '.join(sorted(duplicates))}")
    return seen


def check_source_url(url: str, label: str) -> None:
    if not url.startswith(ALLOWED_SOURCE_PREFIXES):
        fail(f"{label} has unsupported source_url prefix: {url}")
    if url.startswith(("assets/", "data/")):
        local_path = ROOT / url
        if not local_path.exists():
            fail(f"{label} references missing local source file: {url}")


def check_csv_has_rows(path: Path) -> None:
    if not path.exists():
        fail(f"Missing CSV export: {path.relative_to(ROOT)}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        fail(f"CSV export has no data rows: {path.relative_to(ROOT)}")


def main() -> int:
    data = load_json(DATA_JSON)
    missing_keys = sorted(REQUIRED_TOP_LEVEL_KEYS - set(data))
    if missing_keys:
        fail(f"Top-level JSON keys missing: {', '.join(missing_keys)}")

    candidates = data.get("candidates", [])
    records = data.get("records", [])
    stages = data.get("pipeline_stages", [])
    rows = data.get("rows", [])
    columns = data.get("columns", [])
    gaps = data.get("gaps", [])

    if not isinstance(candidates, list) or not candidates:
        fail("JSON must contain at least one candidate")
    if not isinstance(records, list) or not records:
        fail("JSON must contain at least one evidence record")
    if not isinstance(stages, list) or not stages:
        fail("JSON must contain at least one pipeline stage")

    candidate_ids = assert_unique(candidates, "id", "candidates")
    record_ids = assert_unique(records, "id", "records")
    stage_ids = assert_unique(stages, "id", "pipeline_stages")

    matrix_rows = {str(row) for row in rows}
    matrix_columns = {str(column) for column in columns}
    if not matrix_rows or not matrix_columns:
        fail("Matrix rows and columns must be declared")

    for candidate in candidates:
        require_fields(candidate, REQUIRED_CANDIDATE_FIELDS, f"candidate {candidate.get('id', '<unknown>')}")
        if str(candidate["current_stage_id"]) not in stage_ids:
            fail(f"candidate {candidate['id']} uses unknown current_stage_id {candidate['current_stage_id']}")
        check_source_url(str(candidate["source_url"]), f"candidate {candidate['id']}")
        for optional in ("secondary_source_url",):
            if candidate.get(optional):
                check_source_url(str(candidate[optional]), f"candidate {candidate['id']} {optional}")

    for record in records:
        require_fields(record, REQUIRED_RECORD_FIELDS, f"record {record.get('id', '<unknown>')}")
        cid = str(record["candidate_id"])
        if cid not in candidate_ids and cid != "GENERAL-LYME-AWARENESS":
            fail(f"record {record['id']} references unknown candidate_id {cid}")
        if str(record["matrix_row"]) not in matrix_rows:
            fail(f"record {record['id']} uses undeclared matrix_row {record['matrix_row']}")
        if str(record["matrix_column"]) not in matrix_columns:
            fail(f"record {record['id']} uses undeclared matrix_column {record['matrix_column']}")
        check_source_url(str(record["source_url"]), f"record {record['id']}")

    for index, gap in enumerate(gaps, start=1):
        for field in ("matrix_row", "matrix_column", "gap"):
            if not gap.get(field):
                fail(f"gap {index} is missing {field}")
        if str(gap["matrix_row"]) not in matrix_rows:
            fail(f"gap {index} uses undeclared matrix_row {gap['matrix_row']}")
        if str(gap["matrix_column"]) not in matrix_columns:
            fail(f"gap {index} uses undeclared matrix_column {gap['matrix_column']}")

    for path in (PIPELINE_CSV, EVIDENCE_CSV):
        check_csv_has_rows(path)

    if not INDEX_HTML.exists():
        fail("Missing index.html")
    html = INDEX_HTML.read_text(encoding="utf-8")
    for marker in REQUIRED_HTML_MARKERS:
        if marker not in html:
            fail(f"index.html is missing expected marker: {marker}")

    if not SEED_IMAGE.exists():
        fail("Missing seed funnelgram image in assets/")

    print("OK: Lyme vaccine dashboard validation passed")
    print(f"  candidates: {len(candidates)}")
    print(f"  evidence records: {len(record_ids)}")
    print(f"  matrix cells available: {len(matrix_rows) * len(matrix_columns)}")
    print(f"  gaps listed: {len(gaps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
