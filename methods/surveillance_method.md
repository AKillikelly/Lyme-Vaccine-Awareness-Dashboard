# Surveillance and evidence-map method

This dashboard starts from a seed funnelgram image and converts it into a source-backed public awareness evidence map. The seed image is useful for orientation, but the public dashboard should prioritize source-backed, dated records over static slide status text.

## Evidence domains and source types

Records are coded into a matrix using two dimensions:

- **Evidence domain / row:** candidate status, clinical efficacy, clinical safety, immunogenicity or correlates, regulatory and public health guidance, preclinical evidence, manufacturing and access, burden and need, and source status check.
- **Source type / column:** government or regulator, clinical trial registry, peer-reviewed publication, company pipeline or press release, academic or institutional news, and seed funnelgram.

Each record has a stable ID, candidate ID, title, date, source URL, verification status, key finding, evidence signal, and actionability note. The matrix is a navigation and gap-finding device, not a formal systematic review.

## Verification rules

Use these labels consistently:

- **manual source-backed:** A human reviewer checked the linked source and promoted the record into the source-of-truth JSON.
- **seed image / requires verification:** The record came from the funnelgram image and should not be used as current status unless corroborated.
- **unverified surveillance hit:** A scheduled script found the record; a human has not yet coded it.

When a seed record conflicts with newer public sources, keep the seed note visible but make the source-backed status the default display state.

## Weekly source surveillance

The GitHub Actions workflow runs `scripts/update_sources.py` each Monday and on manual dispatch. The script writes dated files into `updates/` and does not automatically edit `data/lyme_vaccine_map_data_v0_1.json`.

Recommended review workflow:

1. Open the newest `updates/surveillance_hits_YYYY-MM-DD.json` file.
2. Check whether any hit changes a candidate stage, population, safety signal, trial status, regulatory status, publication status, or public-health recommendation.
3. Promote only verified records into the JSON data file.
4. Add a concise status-discrepancy note when a source supersedes the seed funnelgram.
5. Run `python scripts/validate_site.py` before publishing.

## Source-watch anchors

Monitor these categories at minimum:

- CDC Lyme disease vaccine page and future ACIP materials.
- FDA, EMA, and other regulatory decisions or advisory committee packets.
- ClinicalTrials.gov records for Lyme vaccine trials.
- Company pipelines and press releases from Pfizer, Valneva, Moderna, Bavarian Nordic, Blue Lake Biotechnology, CyanVac, and future developers.
- Peer-reviewed publications indexed in PubMed or publisher pages.
- Academic news releases that describe preclinical programs, paired with the underlying publication when available.

## Scope limits

This is an awareness dashboard. It is not clinical guidance, investment advice, or a substitute for FDA/EMA/ACIP source documents. Candidate status should be checked against the cited source date before public use.
