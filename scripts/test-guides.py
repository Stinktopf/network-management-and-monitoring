#!/usr/bin/env python3
"""Guard terminal context and keep worked answers out of student tasks."""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalized(text):
    return " ".join(text.split())


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
                        self.assertIn(normalized(expected), normalized(result.stdout))
                        if level == "solution":
                            self.assertIn(guide.stem.upper(), result.stdout)
                            self.assertLess(
                                normalized(result.stdout).index("Worked answer"),
                                normalized(result.stdout).index(normalized(solution)),
                            )
                            self.assertNotIn(task.strip(), result.stdout)
                            self.assertIn("Investigation commands", result.stdout)
                            self.assertIn(normalized(investigation), normalized(result.stdout))
                            self.assertLess(result.stdout.index("Investigation commands"), result.stdout.index("Worked answer"))
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
            for level in ("task", "hint"):
                output = self.render(scenario, 1, level).stdout
                heading = f"1 "
                first_step = next(line for line in output.splitlines() if line.startswith(heading))
                self.assertIn(
                    f"BOB1 / {scenario.upper()} / {level.upper()}\n--------------------------------------------------------------------\n{first_step}",
                    output,
                )
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

    def test_solution_defaults_to_one_step(self):
        result = subprocess.run(
            ["make", "--no-print-directory", "solution", "SCENARIO=networking"],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
            env=dict(os.environ, AI5049_COLOR="never"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 Start on the Lagoon probe", result.stdout)
        self.assertNotIn("2 Resolve the name and fetch the service", result.stdout)
        self.assertIn("Worked answer", result.stdout)
        self.assertIn("make enter NODE=probe01.bob1.lagoontransit.test", result.stdout)
        self.assertIn("Investigation commands", result.stdout)
        self.assertIn(
            "BOB1 / NETWORKING / SOLUTION\n--------------------------------------------------------------------\n"
            "1 Start on the Lagoon probe",
            result.stdout,
        )

    def test_removed_operations_steps_are_rejected_without_remapping(self):
        for step in (6, 7):
            with self.subTest(step=step):
                result = self.render("operations", step, "solution")
                self.assertEqual(result.returncode, 2)
                self.assertIn("Choose STEP=1 through STEP=5", result.stderr)
                self.assertNotIn("4 Confirm the policy", result.stdout)
                self.assertNotIn("5 Prove recovery", result.stdout)

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

    def test_cheatsheet_preserves_copyable_commands(self):
        source = (ROOT / "slides/resources/CHEATSHEET.md").read_text()
        for color in ("never", "always"):
            with self.subTest(color=color):
                result = subprocess.run(
                    ["bash", "scripts/materials.sh", "cheatsheet"], cwd=ROOT,
                    capture_output=True, text=True, check=True,
                    env=dict(os.environ, AI5049_COLOR=color),
                )
                plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
                self.assertNotIn("marp: true", plain)
                self.assertNotIn("```", plain)
                self.assertNotIn("**", plain)
                for code in re.findall(r"```[^\n]*\n(.*?)\n```", source, re.S):
                    self.assertIn("\n".join("  " + line for line in code.splitlines()), plain)
                self.assertIn("make fault-link", plain)
                self.assertIn("make clear-routing", plain)
                self.assertEqual("\x1b[" in result.stdout, color == "always")
                if color == "always":
                    self.assertIn(
                        "\x1b[35mmake networking      \x1b[0m\x1b[90m# follow a request\x1b[0m",
                        result.stdout,
                    )

    def test_inline_command_comments_are_gray(self):
        result = subprocess.run(
            ["bash", "scripts/next-steps.sh", "networking", "1", "hint"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="always"),
        )
        self.assertIn(
            "\x1b[35mip -br addr                       \x1b[0m\x1b[90m# addresses and interface state\x1b[0m",
            result.stdout,
        )

    def test_guide_spacing_is_consistent_across_scenarios(self):
        contexts = ("Inside ", "In the ", "WSL repository:", "Start in WSL:", "Router CLI")
        for scenario in ("networking", "operations", "automation", "monitoring"):
            for level in ("task", "hint", "solution"):
                output = self.render(scenario, "all", level).stdout
                lines = output.splitlines()
                with self.subTest(scenario=scenario, level=level):
                    self.assertFalse(any(lines[i] == lines[i + 1] == "" for i in range(len(lines) - 1)))
                    headings = [
                        i for i, line in enumerate(lines)
                        if line.startswith(contexts) or (line.endswith(":") and line != "Decision:")
                    ]
                    for i in headings:
                        if lines[i - 1] != "":
                            self.assertTrue(
                                lines[i - 1].endswith(":")
                                or lines[i - 1] in ("Worked answer", "Investigation commands")
                            )
                        if lines[i].startswith(contexts):
                            self.assertNotEqual(lines[i + 1], "")
                        elif lines[i + 1] == "":
                            self.assertTrue(lines[i + 2].startswith(contexts) or lines[i + 2].endswith(":"))
                    if level == "solution":
                        titles = [i for i, line in enumerate(lines) if re.match(r"^[1-9] ", line)]
                        answers = [i for i, line in enumerate(lines) if line == "Worked answer"]
                        investigations = [i for i, line in enumerate(lines) if line == "Investigation commands"]
                        self.assertTrue(all(lines[i - 1] == lines[i + 1] == "" for i in titles))
                        self.assertTrue(all(lines[i - 1] == "" and lines[i + 1] != "" for i in answers))
                        self.assertTrue(all(lines[i - 1] == "" and lines[i + 1] != "" for i in investigations))
                    for i, line in enumerate(lines[:-1]):
                        if line.startswith(contexts) or (line.endswith(":") and line != "Decision:"):
                            self.assertNotEqual(lines[i + 1], "")
                    actions = [line for line in lines if "Next worked step:" in line or "When ready:" in line]
                    self.assertTrue(all(line.startswith(("→", "->")) for line in actions))
                    for index, line in enumerate(lines):
                        if "Next worked step:" in line or "When ready:" in line or "Commands and clues:" in line or "Commands and expected results:" in line:
                            self.assertGreater(index, 0)
                            previous_is_action = any(label in lines[index - 1] for label in (
                                "Next worked step:", "When ready:", "Commands and clues:",
                                "Commands and expected results:",
                            ))
                            if not previous_is_action:
                                self.assertEqual(lines[index - 1], "")

    def test_next_steps_use_gold_for_the_label_and_command(self):
        result = subprocess.run(
            ["bash", "scripts/next-steps.sh", "operations", "1", "solution"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="always"),
        )
        self.assertIn(
            "\x1b[36m\x1b[1m→\x1b[0m Next worked step: \x1b[33m\x1b[1mmake solution SCENARIO=operations STEP=2\x1b[0m",
            result.stdout,
        )
        plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
        next_line = next(line for line in plain.splitlines() if "Next worked step:" in line)
        self.assertTrue(next_line.startswith("→ Next worked step:"), next_line)
        task = subprocess.run(
            ["bash", "scripts/next-steps.sh", "operations", "1", "task"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="always"),
        ).stdout
        self.assertIn(
            "Commands and clues: \x1b[33m\x1b[1mmake hint SCENARIO=operations STEP=1\x1b[0m",
            task,
        )
        hint = subprocess.run(
            ["bash", "scripts/next-steps.sh", "operations", "1", "hint"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="always"),
        ).stdout
        self.assertIn(
            "Commands and expected results: \x1b[33m\x1b[1mmake solution SCENARIO=operations STEP=1\x1b[0m",
            hint,
        )

    def test_explanatory_lines_between_commands_are_spaced_and_unstyled(self):
        result = subprocess.run(
            ["bash", "scripts/next-steps.sh", "operations", "4", "solution"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="never"),
        )
        self.assertIn("\ndiff\n\nCommit only if the diff contains this deletion and no unrelated edits:\ncommit now\n", result.stdout)
        self.assertNotIn("\x1b[90mCommit only if", result.stdout)
        self.assertIn("\nWorked answer\nNeighbor 192.0.2.2", result.stdout)

    def test_soft_wrapped_prose_and_section_transitions_render_as_paragraphs(self):
        operations = self.render("operations", 2, "solution").stdout
        self.assertIn(
            "A down peer needs adjacency diagnosis before route-policy analysis. "
            "If links and peers are up, continue to the prefix trace.",
            normalized(operations),
        )
        self.assertIn(
            "If the name does not resolve, check hostname: router SSH belongs on operations01.",
            normalized(operations),
        )
        networking = self.render("networking", "all", "hint").stdout
        self.assertIn(
            "hop alone does not prove that forwarding failed.\n\n"
            "2 Resolve the name and fetch the service",
            networking,
        )
        automation = self.render("automation", 2, "hint").stdout
        self.assertIn(
            "Follow the referenced prefix-set and accept/reject action, not just policy names.",
            normalized(automation),
        )
        monitoring = self.render("monitoring", 6, "hint").stdout
        self.assertIn(
            "Use Add query for the second expression, also in Code mode.",
            normalized(monitoring),
        )

    def test_command_lead_ins_are_petrol_headings(self):
        result = subprocess.run(
            ["bash", "scripts/next-steps.sh", "operations", "4", "solution"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="always"),
        )
        self.assertIn(
            "\x1b[36m\x1b[1mCommit only if the diff contains this deletion and no unrelated edits:\x1b[0m\n\x1b[35mcommit now\x1b[0m",
            result.stdout,
        )

    def test_color_changes_presentation_only(self):
        for scenario in ("networking", "operations", "automation", "monitoring"):
            for level in ("task", "hint", "solution"):
                with self.subTest(scenario=scenario, level=level):
                    plain = self.render(scenario, "all", level).stdout
                    colored = subprocess.run(
                        ["bash", "scripts/next-steps.sh", scenario, "all", level],
                        cwd=ROOT, capture_output=True, text=True, check=True,
                        env=dict(os.environ, AI5049_COLOR="always"),
                    ).stdout
                    self.assertEqual(re.sub(r"\x1b\[[0-9;]*m", "", colored), plain)

    def test_welcome_profile_does_not_repeat_terminal_context(self):
        nodes = (
            "operations01.bob1.reefnet.test",
            "probe01.bob1.lagoontransit.test",
            "probe01.bob1.pacifictransit.test",
            "service01.bob1.oceanresearch.test",
        )
        for node in nodes:
            with self.subTest(node=node):
                result = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-ic",
                     'hostname() { printf "%s\\n" "$TEST_NODE"; }; source "$1"',
                     "bash", str(ROOT / "tools/welcome.sh")],
                    capture_output=True, text=True, timeout=5,
                    env=dict(os.environ, TEST_NODE=node),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_enter_distinguishes_shell_command_errors_from_docker_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            # Replace Docker transport, but run an actual interactive Bash.
            # Skip machine-specific login profiles so this test is portable.
            (bin_dir / "docker").write_text('''#!/bin/sh
case "$1" in
  inspect|cp) exit 0 ;;
  exec)
    if [ -n "${TEST_DOCKER_EXEC_STATUS:-}" ]; then
      exit "$TEST_DOCKER_EXEC_STATUS"
    fi
    shift
    [ "$1" = -it ] || exit 99
    shift 2
    exec "$@"
    ;;
  *) exit 99 ;;
esac
''')
            (bin_dir / "bash").write_text('''#!/bin/sh
if [ "$1" = -l ]; then
  exec /bin/bash --noprofile --norc -i
fi
exec /bin/bash "$@"
''')
            for name in ("docker", "bash"):
                (bin_dir / name).chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}",
                       AI5049_COLOR="never", HISTFILE="/dev/null")
            for commands in ("true\nexit\n", "false\nexit\n",
                             "missing_lab_command_127\nexit\n", "false\n"):
                with self.subTest(commands=commands):
                    result = subprocess.run(
                        ["make", "--no-print-directory", "enter",
                         "NODE=probe01.bob1.lagoontransit.test"], cwd=ROOT,
                        input=commands, text=True, capture_output=True, env=env, timeout=5,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    if "missing_lab_command_127" in commands:
                        self.assertIn("command not found", result.stderr)
            for status in (1, 125, 126, 127):
                with self.subTest(docker_status=status):
                    result = subprocess.run(
                        ["/bin/bash", str(ROOT / "scripts/enter.sh"),
                         "probe01.bob1.lagoontransit.test"], cwd=ROOT,
                        text=True, capture_output=True, timeout=5,
                        env=dict(env, TEST_DOCKER_EXEC_STATUS=str(status)),
                    )
                    self.assertEqual(result.returncode, status, result.stderr)


if __name__ == "__main__":
    unittest.main()
