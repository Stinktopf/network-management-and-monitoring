#!/usr/bin/env python3
"""Guard terminal context and keep worked answers out of student tasks."""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Guides(unittest.TestCase):
    def render(self, scenario, step, level="task"):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/next-steps.sh"), scenario, str(step), level],
                cwd=directory, capture_output=True, text=True, timeout=5,
                env=dict(os.environ, AI5049_COLOR="never"),
            )
            self.assertEqual(list(Path(directory).iterdir()), [])
            return result

    def test_every_step_has_separate_task_hint_and_solution(self):
        for guide in sorted((ROOT / "scripts/guides").glob("*.txt")):
            source = guide.read_text()
            sections = re.split(r"^@@ \d+ .*\n", source, flags=re.M)[1:]
            for step, section in enumerate(sections, 1):
                task, rest = section.split("@@ hint\n")
                hint, rest = rest.split("@@ investigation\n")
                investigation, solution = rest.split("@@ solution\n")
                for level, expected in (("task", task), ("hint", hint), ("solution", solution)):
                    with self.subTest(scenario=guide.stem, step=step, level=level):
                        result = self.render(guide.stem, step, level)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertIn(expected.strip(), result.stdout)
                        if level == "solution":
                            self.assertIn(task.strip(), result.stdout)
                            self.assertIn(investigation.strip(), result.stdout)
                            self.assertLess(result.stdout.index(task.strip()), result.stdout.index(solution.strip()))
                        else:
                            self.assertNotIn(investigation.strip(), result.stdout)
                            self.assertNotIn(solution.strip(), result.stdout)

    def test_entry_is_short_and_hints_offer_commands_without_results(self):
        for scenario in ("networking", "operations", "automation", "monitoring"):
            task = self.render(scenario, 1).stdout
            self.assertLessEqual(len(task.splitlines()), 18)
            self.assertNotIn("Investigation steps", task)
            self.assertNotIn("make solution", task)
            hint = self.render(scenario, 1, "hint").stdout
            self.assertIn("Inside", hint)
            self.assertIn("make solution", hint)
        task = self.render("operations", 1).stdout
        self.assertNotIn("export", task.lower())
        self.assertIn("make enter NODE=probe01.bob1.lagoontransit.test", task)
        hint = self.render("operations", 1, "hint").stdout
        self.assertIn("ping -4", hint)
        self.assertIn("ping -6", hint)
        self.assertNotIn("FAIL", hint)

    def test_worked_investigation_includes_commands_and_keeps_scenario(self):
        output = self.render("operations", 3, "solution").stdout
        self.assertIn("make enter NODE=edge01.bob1.reefnet.test", output)
        self.assertIn("show network-instance default protocols bgp routes ipv4 prefix 198.51.100.0/24", output)
        self.assertIn("show network-instance default route-table ipv4-unicast prefix 198.51.100.0/24", output)
        self.assertIn("make solution SCENARIO=operations STEP=4", output)
        self.assertNotIn("Worked answer: make solution", output)

    def test_student_incident_guide_does_not_give_away_the_repair(self):
        for scenario in ("operations", "automation"):
            output = self.render(scenario, "all").stdout
            for spoiler in ("BLOCK-CUSTOMER-V4", "commit now", "set --delete", "delete / network-instance"):
                self.assertNotIn(spoiler, output)
            self.assertIn("BLOCK-CUSTOMER-V4", self.render(scenario, "all", "solution").stdout)

    def test_invalid_requests_fail(self):
        for args in (("unknown", 1), ("operations", 0), ("operations", 99),
                     ("operations", "../x"), ("operations", 1, "unknown")):
            self.assertEqual(self.render(*args).returncode, 2)

    def test_welcome_matches_the_actual_node(self):
        roles = {
            "operations01.bob1.reefnet.test": "Operator workstation",
            "probe01.bob1.lagoontransit.test": "External service probe",
            "probe01.bob1.pacifictransit.test": "External service probe",
            "service01.bob1.oceanresearch.test": "Customer service",
        }
        for node, role in roles.items():
            with self.subTest(node=node):
                result = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-ic",
                     'hostname() { printf "%s\\n" "$TEST_NODE"; }; source "$1"',
                     "bash", str(ROOT / "tools/welcome.sh")],
                    capture_output=True, text=True, timeout=5,
                    env=dict(os.environ, TEST_NODE=node),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"AI5049 · {node}", result.stdout)
                self.assertIn(role, result.stdout)
                if node.startswith("probe"):
                    self.assertNotIn("Operator workstation", result.stdout)
                    self.assertNotIn("  ssh ", result.stdout)
                    self.assertIn("exit", result.stdout)


if __name__ == "__main__":
    unittest.main()
