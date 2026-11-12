# Groundwater Stress Early-Warning System (India)

**Business question:** which districts will see their water table fall further, and where should the Central Ground Water Board (CGWB) act first?

**Data (both from India Data Portal, not included because of size):**
- CGWB depth-to-water-level readings (550,850 rows, 24,238 wells, 567 districts) saved as `data/raw/cgwb-changes-in-depth-to-water-level.csv`.
- Daily district rainfall, India-WRIS / IMD (3.58 million rows, 628 districts, 2009 to 2024) saved as `data/raw/daily-rainfall-data-district-level.csv`. Only the `actual` column is used: `rfs` is not rainfall and `deviation` explodes when the normal is near zero. Districts join on LGD `district_code` (99.5% match).

The aggregated rainfall table (`data/rain_district_year.csv`) is committed, so the pipeline also runs without the raw rainfall file.

## Pipeline
| Step | File | What it does |
|---|---|---|
| 1 | `scripts/01_clean.py` | Drops 819 impossible depths (<0 or >100 m), builds a unique well ID (names repeat), collapses daily/duplicate readings to well x year x season, keeps 2013-2019 (2020 has only 12 pre-monsoon wells). |
| 2 | `scripts/02_stats.py` | Per-district Sen's slope and Kendall tau (Mann-Kendall) on annual pre-monsoon depth; seasonal recovery; Wilcoxon test. |
| 2b | `scripts/02b_rainfall_prep.py` | Aggregates daily rainfall to district x year (monsoon, pre, post, annual); drops periods with under 80% of days observed. |
| 2c | `scripts/02c_rain_analysis.py` | District fixed-effects regression of recovery on monsoon rainfall anomaly with cluster-robust SEs; rainfall trend vs water-table trend. |
| 3 | `scripts/03_models.py` | Model A: well-level forecast of next pre-monsoon depth. Model B: district deterioration-risk classifier. Both are compared with and without rainfall features. |
| 4 | `sql/queries.sql`, `sql/run_sql.py` | Six KPI queries (window functions, LAG, cumulative share) on SQLite. Results in `reports/sql_results.txt`. |
| 5 | `scripts/04_build_dashboard.py` | Builds the interactive dashboard in `dashboard/dashboard.html`. |

Quick start (recommended): `pip install -r requirements.txt` then `python run_all.py`. Manual order: `python scripts/01_clean.py && python scripts/02_stats.py && python scripts/02b_rainfall_prep.py && python scripts/02c_rain_analysis.py && python scripts/03_models.py && python sql/run_sql.py && python scripts/04_build_dashboard.py`

## Key results
- 135 of 567 districts have a pre-monsoon water table deeper than 10 m (2017-19). 74 districts deepen significantly (Mann-Kendall p < 0.1); 26 improve.
- Punjab deepens fastest (about 0.43 m/yr on average), then Haryana (0.29) and Telangana (0.28). 56 districts are flagged Critical (High risk and deeper than 10 m), 15 of them in Punjab and 9 in Haryana.
- Rajasthan, Punjab and Gujarat hold 46% of all pre-monsoon readings deeper than 20 m.
- **Forecast model (tested on unseen 2018-19):** MAE 1.65 m vs 1.81 m for "same as last year" (9% better); R² 0.883. Within-1 m accuracy is about the same (52%), so the gain is mainly on large errors.
- **Risk classifier:** cross-validated AUC 0.776 (random forest) vs 0.729 (logistic) vs 0.573 (trend-only rule).

## Rainfall findings (IMD / India-WRIS)
- **Rainfall strongly drives recovery.** A monsoon 10% above a district's normal lifts the water table by an extra 0.28 m that year (95% CI 0.252 to 0.307; 511 districts, district fixed effects, cluster-robust SEs). Dropping the implausible district-years above 5,000 mm leaves it unchanged. Next year's pre-monsoon level is 0.229 m shallower. In 85.6% of districts the two series are positively correlated.
- **Most deepening is not a rainfall story.** 72 of 74 districts with a significant deepening trend show no significant fall in monsoon rainfall (only 2 do). This points towards extraction, led by Uttar Pradesh, Punjab, Maharashtra and Haryana, but it is a hypothesis: there is no pumping data and the test covers 7 years.
- **Rainfall barely improves prediction.** Forecast MAE 1.661 m with rainfall vs 1.651 m without; classifier AUC 0.779 vs 0.773, a gain about the size of the split-to-split noise (SD about 0.008). Last year's well levels already carry most of the signal. Reporting this null result is deliberate.

## Honest limits
- The national pre-monsoon trend is **not** statistically significant (tau 0.43, p = 0.24, 7 years). The story is regional, not national.
- Median seasonal recovery was higher in 2017-19 than in 2013-16 (Wilcoxon p < 0.001 on 14,886 wells), so "recovery is shrinking" is not supported.
- Risk score is a screening index, not a calibrated probability. The final scoring window (2016-19) overlaps the training features, so treat the scores as rankings.
- Longitude, latitude and mean monsoon rainfall rank high in feature importance; they stand in for regional geology and cropping, not a causal driver.
- Wells are monitoring points, not a census. No pumping or crop data is included.
- Permutation importance is used instead of SHAP (not installed in this environment).

## Resume bullets
- Cleaned 5.5 lakh CGWB groundwater readings (24k wells, 567 districts) and resolved duplicate well IDs and sensor outliers.
- Linked IMD rainfall to groundwater: a monsoon 10% above normal adds 0.28 m of recovery (fixed effects, 511 districts); 72 of 74 deepening districts show no matching rainfall decline.
- Applied Mann-Kendall and Sen's slope across 518 districts; identified 74 with significant deepening, concentrated in Punjab and Haryana.
- Built a time-split gradient boosting forecast (MAE 1.65 m vs 1.81 m baseline) and a random forest district risk classifier (AUC 0.776).
- Designed an interactive map dashboard with state zoom, risk tiers and a priority list.


## Quick start
```bash
pip install -r requirements.txt
# save the raw CSV as data/raw/cgwb-changes-in-depth-to-water-level.csv
python run_all.py          # cleans, analyses, models, builds the site, runs 14 checks (about 30 s)
```
Then open `docs/index.html`.

## Live demo
Add your link here after deploying: `https://<your-username>.github.io/<repo-name>/`

### Deploy free on GitHub Pages
1. Create a new GitHub repository and push this folder (the raw CSV is git-ignored).
2. Repository **Settings → Pages → Build and deployment → Deploy from a branch**.
3. Choose branch `main` and folder `/docs`, then Save. The site goes live in about a minute.
4. Replace `YOUR NAME` in `LICENSE` and paste the live link above.

## Project structure
```
run_all.py            one-command pipeline
scripts/              01 clean, 02 stats, 03 models, 04 dashboard build, 05 package site
scripts/02b, 02c      rainfall aggregation and rainfall-vs-groundwater analysis
sql/                  KPI queries and SQLite runner
tests/                14 sanity checks (python -m unittest discover tests -v)
data/                 cleaned outputs (raw file is git-ignored)
models/metrics.json   model scores
reports/              statistics and SQL results
dashboard/            template and generated pages
docs/                 deployable site for GitHub Pages
.github/workflows/    CI that runs the tests on every push
```

## Roadmap
- Add pumping, farm-electricity or crop-area data to test the extraction hypothesis directly.
- Rainfall is a gridded district average and hides local variation; a few Meghalaya and Konkan district-years look too wet.
