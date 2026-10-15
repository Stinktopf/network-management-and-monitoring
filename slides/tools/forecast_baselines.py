"""Baseline, MASE and interval figures for the 11 December slides.

Reads the synthetic series and the persistence/ridge predictions in
assets/data/ and writes forecast-baselines.json. Standard library only.
"""
import csv, json, math
from pathlib import Path

D = Path(__file__).resolve().parents[1] / 'assets/data'
PERIOD, SHIFT_S = 60, 540
series = [float(r['observed_mbps']) if r['observed_mbps'] else None
          for r in csv.DictReader(open(D / 'forecast-synthetic.csv'))]
predictions = [r for r in csv.DictReader(open(D / 'forecast-predictions.csv'))
               if r['actual'] and r['persistence'] and r['ridge']]
slots = [int(r['time_s']) for r in predictions]
ridge = {int(r['time_s']): float(r['ridge']) for r in predictions}

def mean_abs(pairs):
    pairs = [(a, f) for a, f in pairs if a is not None and f is not None]
    return sum(abs(a - f) for a, f in pairs) / len(pairs), len(pairs)

# MASE scale: in-sample one-step naive error on the training data (< 360 s).
scale, _ = mean_abs((series[t], series[t - 1]) for t in range(1, 360))
methods = {
    'persistence': lambda t: series[t - 1],
    'seasonal_naive': lambda t: series[t - PERIOD],
    'ridge': lambda t: ridge[t],
}
result = {'source': 'synthetic teaching data, not a real network measurement',
          'period_s': PERIOD, 'shift_s': SHIFT_S, 'mase_scale_mbps': scale, 'mase': {}}
# Compare all three methods on the same slots: the seasonal value must exist too.
common = [t for t in slots if series[t - PERIOD] is not None]
for name, part in [('before_shift', [t for t in common if t < SHIFT_S]),
                   ('after_shift', [t for t in common if t >= SHIFT_S])]:
    result['mase'][name] = {}
    for method, forecast in methods.items():
        mae, n = mean_abs((series[t], forecast(t)) for t in part)
        result['mase'][name][method] = {'n': n, 'mae_mbps': mae, 'mase': mae / scale}

# Horizon: last value h seconds earlier versus the value one period earlier.
result['horizon_before_shift'] = []
for h in [1, 5, 10, 30]:
    window = range(480, SHIFT_S)
    last, _ = mean_abs((series[t], series[t - h]) for t in window)
    seasonal, _ = mean_abs((series[t], series[t - PERIOD]) for t in window)
    result['horizon_before_shift'].append({'horizon_s': h, 'persistence_mae_mbps': last,
                                           'seasonal_naive_mae_mbps': seasonal})

# Split-conformal 90% interval for persistence, calibrated on validation (360-479 s).
errors = sorted(abs(series[t] - series[t - 1]) for t in range(360, 480)
                if series[t] is not None and series[t - 1] is not None)
q = errors[math.ceil((len(errors) + 1) * 0.9) - 1]
result['interval'] = {'level': 0.9, 'calibration_errors': len(errors), 'half_width_mbps': q}
for name, part in [('before_shift', [t for t in slots if t < SHIFT_S]),
                   ('after_shift', [t for t in slots if t >= SHIFT_S])]:
    inside = sum(abs(series[t] - series[t - 1]) <= q for t in part)
    result['interval'][name] = {'covered': inside, 'n': len(part)}

# Diebold-Mariano test, absolute loss, ridge minus persistence, with the
# Harvey-Leybourne-Newbold small-sample correction for one-step forecasts.
result['diebold_mariano'] = {}
for name, part in [('before_shift', [t for t in slots if t < SHIFT_S]),
                   ('after_shift', [t for t in slots if t >= SHIFT_S])]:
    d = [abs(series[t] - ridge[t]) - abs(series[t] - series[t - 1]) for t in part]
    n = len(d)
    mean = sum(d) / n
    variance = sum((x - mean) ** 2 for x in d) / n
    dm = mean / math.sqrt(variance / n)
    result['diebold_mariano'][name] = {'n': n, 'mean_loss_difference_mbps': mean,
                                       'dm': dm, 'dm_hln': dm * math.sqrt((n - 1) / n)}

(D / 'forecast-baselines.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result['interval']))
