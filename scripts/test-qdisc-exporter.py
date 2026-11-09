#!/usr/bin/env python3
"""Regression checks for missing queues, counter resets and endpoint identity."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("qdisc", ROOT / "tools/qdisc_exporter.py")
qdisc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qdisc)
SOURCE = "edge01.bob1.lagoontransit.test"
MODEL = json.loads((ROOT / "tools/bob1_model.json").read_text())
PORTS = qdisc.endpoints(MODEL, SOURCE)


class QueueMetrics(unittest.TestCase):
    def sample(self, drops, **overrides):
        return dict(kind="netem", dev="e1-1", root=True, drops=drops, **overrides)

    def test_both_sides_of_all_capacity_links(self):
        ports = [qdisc.endpoints(MODEL, n["fqdn"]) for n in MODEL["nodes"].values()]
        self.assertEqual(sum(map(len, ports)), 6)
        self.assertEqual(PORTS, {"e1-1": ("ethernet-1/1", "lagoon")})

    def test_actual_drops_not_overlimits(self):
        output = qdisc.metrics([self.sample(42, overlimits=999)], PORTS, SOURCE)
        self.assertIn('link_id="lagoon"} 42\n', output)
        self.assertNotIn("999", output)

    def test_missing_queue_is_not_zero_drops(self):
        output = qdisc.metrics([], PORTS, SOURCE)
        self.assertIn('link_id="lagoon"} 0\n', output)
        self.assertFalse(any(line.startswith("reefnet_qdisc_dropped_packets_total{") for line in output.splitlines()))

    def test_children_are_not_double_counted(self):
        child = dict(kind="netem", dev="e1-1", parent="1:1", drops=42)
        output = qdisc.metrics([self.sample(42), child], PORTS, SOURCE)
        self.assertEqual(output.count('link_id="lagoon"} 42\n'), 1)

    def test_reset_exposes_new_raw_counter(self):
        qdisc.metrics([self.sample(42)], PORTS, SOURCE)
        output = qdisc.metrics([self.sample(0)], PORTS, SOURCE)
        self.assertIn('reefnet_qdisc_dropped_packets_total{', output)
        self.assertIn('link_id="lagoon"} 0\n', output)

    def test_malformed_counter_fails_collection(self):
        with self.assertRaises(ValueError):
            qdisc.metrics([self.sample(-1)], PORTS, SOURCE)
        with self.assertRaises(KeyError):
            qdisc.metrics([dict(kind="netem", dev="e1-1", root=True)], PORTS, SOURCE)


if __name__ == "__main__":
    unittest.main()
