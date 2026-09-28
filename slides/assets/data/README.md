# Recovered forecast evidence

These files were supplied with the reference course under `slides/Kursreferenzen/Technik/labs/results/offline/`:

- `forecast-synthetic.csv`: synthetic teaching series, seed 5049.
- `forecast-predictions.csv`: observed values and persistence/ridge predictions.
- `forecast-summary.json`: split, evaluation policy and reported results.

Training precedes 360 s, validation precedes 480 s, and the shown test interval is 480–599 s. Both methods are evaluated on the same 110 of 120 slots. Missing targets or any of the three input lags exclude a slot. The plot preserves the source data and exclusion windows.

This is an offline teaching example, not traffic captured from BOB1. No runtime command or Python filename appears on the student-facing slides.
