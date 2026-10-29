# Teaching data

These are synthetic examples, not measurements from the running lab.

| File | Contents |
|---|---|
| `forecast-synthetic.csv` | Synthetic traffic series, seed 5049 |
| `forecast-predictions.csv` | Observed values and persistence/ridge predictions |
| `forecast-summary.json` | Split, evaluation policy and results |
| `forecast-baselines.json` | Seasonal naive, MASE, horizon and 90% interval coverage |
| `sampling-runs.csv` | Fault phases and detection delays from the timing model |

The forecast example uses training data before 360 s and validation data before 480 s. The test interval is 480–599 s. Both methods are evaluated on the same 110 of 120 slots. Missing targets or any of the three input lags exclude a slot.

`python3 slides/tools/forecast_baselines.py` regenerates `forecast-baselines.json` from the two forecast CSV files. MASE is scaled by the one-step naive error on the training data. The interval is split-conformal, calibrated on the validation errors.

Comparisons use matched available inputs. MASE includes seasonal naive, leaving 55 slots before and 53 after the shift. Ridge versus persistence uses 55 in each period. The JSON records the sample size for each forecast horizon. Loss differences are descriptive, with no significance claim based on independent time slots. Conformal coverage is observed coverage in this synthetic time series, not a demonstrated exchangeability guarantee.

`npm run sampling` regenerates the sampling data: 120 fault phases, a 5 s fault duration, and either regular 5 s probes or alternating 4 s / 6 s intervals. It does not run network probes.
