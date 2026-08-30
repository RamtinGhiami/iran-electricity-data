# Iran's Electricity Deficit

Data, pipeline and (forthcoming) paper on Iran's electricity imbalance:
how large the peak deficit becomes if current trends continue, and what
closing it would require.

See **[`PIPELINE.md`](PIPELINE.md)** for the stage-by-stage pipeline, definitions and headline results. The
readable walkthrough is `notebooks/FULL_PIPELINE.ipynb`
(from library setup to the deficit forecast, with commentary).

Headline state: peak deficit reached **17.6 GW (21.9% of demand) in 1403**
and 14.9 GW in 1404; on current trends it projects to **~28 GW by 1408**
and **~41 GW by 1412** (95% bootstrap bands in
`results/deficit_forecast_summary.json`).

Manually collected official sources are registered in
`manual-data/PROVENANCE.md`.
