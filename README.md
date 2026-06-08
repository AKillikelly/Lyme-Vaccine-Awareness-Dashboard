# Lyme Vaccine Development Awareness Dashboard

A static GitHub Pages dashboard for communicating the Lyme disease vaccine pipeline, source status, evidence gaps, and public-health watch items.

The dashboard is seeded from a funnelgram image and converted into a source-backed evidence map inspired by the RSV Evidence Map pattern: update status, source inventory, filters, evidence matrix, record cards, gap tracking, and provenance.

## What is included

```text
.
├── index.html                                  # Single-page dashboard for GitHub Pages
├── assets/funnelgram_seed.png                  # Original seed funnelgram image
├── data/lyme_vaccine_map_data_v0_1.json        # Source-of-truth dashboard data
├── data/lyme_vaccine_pipeline_seed_v0_1.csv    # Candidate/pipeline CSV export
├── data/lyme_vaccine_evidence_records_v0_1.csv # Evidence-record CSV export
├── methods/surveillance_method.md              # Coding and review method
├── scripts/validate_site.py                    # Pre-deployment validation
├── scripts/update_sources.py                   # Weekly unverified surveillance-hit collector
└── .github/workflows/pages.yml                 # GitHub Pages deployment workflow
```

## Dashboard features

- Source-backed pipeline cards by development stage.
- Status reconciliation between the seed funnelgram and current public sources.
- Filterable candidate table.
- Clickable evidence matrix for gap spotting.
- Filterable evidence-record cards with source links and stable IDs.
- Priority gap list.
- Methods and provenance section with CSV/JSON exports.
- Weekly GitHub Actions surveillance output for ClinicalTrials.gov and PubMed.

## Publish on GitHub Pages

1. Create a new GitHub repository.
2. Copy all files from this folder into the repository root.
3. Commit and push to the `main` branch.
4. In GitHub, open **Settings → Pages** and set **Source** to **GitHub Actions**.
5. In **Settings → Actions → General**, allow workflow read/write permissions if you want the scheduled surveillance job to commit files into `updates/`.
6. Open the **Actions** tab and run **Validate and publish dashboard**, or push a change to `main`.

GitHub Pages requires a top-level entry file such as `index.html`; this repository already includes one.

## Local validation

Run:

```bash
python scripts/validate_site.py
```

For a local preview, serve the repository root with any static file server, for example:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/`.

## Data update workflow

The authoritative data file is `data/lyme_vaccine_map_data_v0_1.json`. The update script writes candidate hits into `updates/` only. It does not promote unverified records into the dashboard.

Manual update checklist:

1. Review new `updates/surveillance_hits_YYYY-MM-DD.json` files.
2. Confirm the source and date.
3. Add or edit a record in `data/lyme_vaccine_map_data_v0_1.json`.
4. Update CSV exports if needed.
5. Run `python scripts/validate_site.py`.
6. Commit and push.

## Seed status reconciliation notes

The seed funnelgram is retained as a provenance artifact. Several records intentionally distinguish seed-map status from more current public-source status:

- LB6V / VLA15 is shown as the most advanced candidate, with Phase 3 results and planned regulatory submissions, rather than as an approved or marketed product.
- Moderna's mRNA-1975 and mRNA-1982 records are treated as current pipeline-stage records, not just as historical Phase 1/2 seed-map records.
- Bavarian Nordic is flagged because older 2026 clinical-entry wording differs from later public reporting that moves expected clinical development to 2027.

## Disclaimer

This dashboard is for public awareness and evidence tracking only. It is not clinical guidance, regulatory advice, or investment advice. Always use the dated, linked source records for public claims.
