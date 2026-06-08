#!/usr/bin/env python3
"""Collect unverified Lyme vaccine surveillance hits.

This script is intentionally conservative: it writes new candidate hits into
updates/ for human review and does not modify the source-of-truth evidence map.
Use it in a scheduled GitHub Action to create a transparent audit trail of new
ClinicalTrials.gov and PubMed records that may deserve promotion into data/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
UPDATES_DIR = ROOT / "updates"
USER_AGENT = "lyme-vaccine-awareness-dashboard/0.1 (+https://github.com/)"

CLINICALTRIALS_QUERY = {
    "query.cond": "Lyme Disease",
    "query.intr": "vaccine",
    "pageSize": "50",
    "format": "json",
}

PUBMED_TERM = '((Lyme disease[Title/Abstract] OR Borrelia burgdorferi[Title/Abstract]) AND vaccine[Title/Abstract])'

DEVELOPER_WATCHLIST = [
    {
        "name": "CDC Lyme vaccine page",
        "url": "https://www.cdc.gov/lyme/about/lyme-disease-vaccine.html",
        "why_watch": "Public health status, ACIP process, and vaccine availability wording.",
    },
    {
        "name": "Valneva LB6V candidate page",
        "url": "https://valneva.com/research-development/lyme-disease/",
        "why_watch": "Candidate overview, regulatory status, and partner updates.",
    },
    {
        "name": "Moderna pipeline",
        "url": "https://www.modernatx.com/en-US/research/pipeline",
        "why_watch": "mRNA-1975 and mRNA-1982 development phase changes.",
    },
    {
        "name": "Bavarian Nordic pipeline and reports",
        "url": "https://www.bavarian-nordic.com/investor/reports.aspx",
        "why_watch": "Early-stage Lyme candidate entry into clinical development.",
    },
    {
        "name": "Blue Lake Biotechnology news",
        "url": "https://www.bluelakebio.com/news",
        "why_watch": "PIV5-based intranasal Lyme vaccine preclinical updates.",
    },
    {
        "name": "Tufts Now Lyme vaccine updates",
        "url": "https://now.tufts.edu/",
        "why_watch": "CspZ-targeted preclinical vaccine research updates.",
    },
]


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def fetch_json(url: str, timeout: int = 25) -> tuple[dict[str, Any] | None, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed public URLs built below
            body = response.read().decode("utf-8")
        return json.loads(body), None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def clinicaltrials_hits() -> dict[str, Any]:
    url = "https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(CLINICALTRIALS_QUERY)
    payload, error = fetch_json(url)
    hits: list[dict[str, Any]] = []
    if payload:
        for study in payload.get("studies", []):
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            arms = protocol.get("armsInterventionsModule", {})
            conditions = protocol.get("conditionsModule", {})
            sponsors = protocol.get("sponsorCollaboratorsModule", {})
            hits.append(
                {
                    "source": "ClinicalTrials.gov API",
                    "nct_id": identification.get("nctId"),
                    "title": identification.get("briefTitle"),
                    "overall_status": status.get("overallStatus"),
                    "phase": ", ".join(design.get("phases", [])) if isinstance(design.get("phases"), list) else design.get("phases"),
                    "conditions": conditions.get("conditions", []),
                    "interventions": [item.get("name") for item in arms.get("interventions", []) if item.get("name")],
                    "lead_sponsor": sponsors.get("leadSponsor", {}).get("name"),
                    "last_update_submit_date": status.get("lastUpdateSubmitDate"),
                    "url": f"https://clinicaltrials.gov/study/{identification.get('nctId')}" if identification.get("nctId") else None,
                    "review_status": "unverified surveillance hit",
                }
            )
    return {"query_url": url, "error": error, "hit_count": len(hits), "hits": hits}


def pubmed_hits(max_results: int = 20) -> dict[str, Any]:
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    esearch_params = {
        "db": "pubmed",
        "term": PUBMED_TERM,
        "retmode": "json",
        "sort": "pub+date",
        "retmax": str(max_results),
    }
    esearch_url = base + "esearch.fcgi?" + urllib.parse.urlencode(esearch_params)
    search_payload, search_error = fetch_json(esearch_url)
    ids = []
    if search_payload:
        ids = search_payload.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return {"query_url": esearch_url, "error": search_error, "hit_count": 0, "hits": []}

    esummary_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
    esummary_url = base + "esummary.fcgi?" + urllib.parse.urlencode(esummary_params)
    summary_payload, summary_error = fetch_json(esummary_url)
    hits: list[dict[str, Any]] = []
    if summary_payload:
        result = summary_payload.get("result", {})
        for pmid in result.get("uids", []):
            item = result.get(pmid, {})
            hits.append(
                {
                    "source": "PubMed E-utilities",
                    "pmid": pmid,
                    "title": item.get("title"),
                    "journal": item.get("fulljournalname"),
                    "pubdate": item.get("pubdate"),
                    "authors": [a.get("name") for a in item.get("authors", [])[:5] if a.get("name")],
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "review_status": "unverified surveillance hit",
                }
            )
    return {
        "query_url": esearch_url,
        "summary_url": esummary_url,
        "error": search_error or summary_error,
        "hit_count": len(hits),
        "hits": hits,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Write a metadata-only surveillance file without web requests.")
    args = parser.parse_args(argv)

    UPDATES_DIR.mkdir(exist_ok=True)
    now = utc_now()
    outfile = UPDATES_DIR / f"surveillance_hits_{now.date().isoformat()}.json"

    report: dict[str, Any] = {
        "generated_at_utc": now.isoformat(),
        "review_rule": "Records in this file are unverified surveillance hits. Manually review sources before promoting anything into data/lyme_vaccine_map_data_v0_1.json.",
        "watchlist": DEVELOPER_WATCHLIST,
        "sources": {},
    }

    if args.offline:
        report["sources"] = {
            "clinicaltrials": {"error": "offline mode", "hit_count": 0, "hits": []},
            "pubmed": {"error": "offline mode", "hit_count": 0, "hits": []},
        }
    else:
        report["sources"] = {
            "clinicaltrials": clinicaltrials_hits(),
            "pubmed": pubmed_hits(),
        }

    outfile.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total_hits = sum(source.get("hit_count", 0) for source in report["sources"].values())
    print(f"Wrote {outfile.relative_to(ROOT)} with {total_hits} unverified surveillance hits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
