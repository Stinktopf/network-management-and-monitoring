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
                task, rest = section.split("@@ start\n")
                start, rest = rest.split("@@ hint\n")
                hint, rest = rest.split("@@ investigation\n")
                investigation, solution = rest.split("@@ solution\n")
                for level, expected in (("task", task + start), ("hint", hint), ("solution", solution)):
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
                            self.assertNotIn(start.strip(), result.stdout)
                            self.assertIn("Investigation commands", result.stdout)
                            self.assertIn(normalized(investigation), normalized(result.stdout))
                            self.assertLess(result.stdout.index("Investigation commands"), result.stdout.index("Worked answer"))
                        else:
                            self.assertNotIn(investigation.strip(), result.stdout)
                            self.assertNotIn(solution.strip(), result.stdout)

    def test_task_commands_appear_in_hint_and_solution(self):
        # The task names each command. The hint and the solution show it with arguments.
        for guide in sorted((ROOT / "scripts/guides").glob("*.txt")):
            source = guide.read_text()
            for step, section in enumerate(re.split(r"^@@ \d+ .*\n", source, flags=re.M)[1:], 1):
                start = section.split("@@ start\n")[1].split("@@ hint\n")[0]
                hint = section.split("@@ hint\n")[1].split("@@ investigation\n")[0]
                investigation = section.split("@@ investigation\n")[1].split("@@ solution\n")[0]
                block = start.split("Commands:\n")[1].split("\n\n")[0]
                hint = re.sub(r"\\\n\s*", " ", hint)
                investigation = re.sub(r"\\\n\s*", " ", investigation)
                for line in block.splitlines():
                    # Headings name the device. Indented lines list its commands.
                    if not line.startswith("  ") or "route commands from" in line:
                        continue
                    for command in line.strip().split(", "):
                        command = re.sub(r" <[^>]+>", "", command.split(" for ")[0])
                        words = command.split()
                        for level, text in (("hint", start + hint), ("solution", start + investigation)):
                            with self.subTest(scenario=guide.stem, step=step, level=level, command=command):
                                def runs(line):
                                    tokens = line.split()
                                    starts = (tokens[:1] == words[:1] or f"| {words[0]} " in line + " "
                                              or f"$({words[0]} " in line)
                                    return starts and all(w in tokens for w in words[1:])
                                self.assertTrue(
                                    any(runs(l.strip()) for l in text.splitlines()),
                                    f"{command!r} missing from {level}",
                                )

    def test_hint_and_solution_use_the_same_commands(self):
        # The worked solution runs exactly the hint's commands. <placeholder> stands for any value.
        command = re.compile(r"^  (make |show |info |enter |delete |set |discard |commit|diff$|date |ip |ping |dig "
                             r"|traceroute |tracepath |mtr |curl |gnmic |cat |tail |jq |getent |hostname$|ssh "
                             r"|[A-Z_][A-Z0-9_]*=)")
        def commands(text):
            text = re.sub(r"\\\n\s*", " ", text)
            found = []
            for line in text.splitlines():
                if command.match(line):
                    found.append(" ".join(re.sub(r"\s+#.*$", "", line).split()))
            return set(found)
        def pattern(line):
            return re.compile("^" + re.sub(r"<[^>]+>", ".+", re.escape(line).replace("\\<", "<").replace("\\>", ">")) + "$")
        for guide in sorted((ROOT / "scripts/guides").glob("*.txt")):
            source = guide.read_text()
            for step, section in enumerate(re.split(r"^@@ \d+ .*\n", source, flags=re.M)[1:], 1):
                # The task's start block sets up the experiment. The hint continues from there.
                start = section.split("@@ start\n")[1].split("@@ hint\n")[0]
                hint = commands(start.split("Start in WSL:")[-1] + section.split("@@ hint\n")[1].split("@@ investigation\n")[0])
                solution = commands(section.split("@@ investigation\n")[1].split("@@ solution\n")[0])
                with self.subTest(scenario=guide.stem, step=step):
                    only_hint = {h for h in hint if not any(pattern(h).match(x) for x in solution)}
                    only_solution = {x for x in solution if not any(pattern(h).match(x) for h in hint)}
                    self.assertEqual((only_hint, only_solution), (set(), set()))

    def test_both_probes_run_the_same_checks(self):
        # A Pacific block repeats the Lagoon block in full. Only the gateway differs.
        def probe_blocks(text):
            blocks, current = {}, None
            for line in text.splitlines():
                if line.startswith(("Inside", "In the")):
                    current = ("pacific" if "Pacific probe" in line else
                               "lagoon" if "Lagoon probe" in line or re.search(r"\bthe probe\b", line) else None)
                    if current:
                        blocks.setdefault(current, [])
                elif current and line.startswith("  ") and line.strip():
                    command = line.split("#")[0].strip()
                    command = re.sub(r"203\.0\.113\.(129|1)\b", "GATEWAY", command)
                    blocks[current].append(re.sub(r"2001:db8:[ab]::1\b", "GATEWAY6", command))
                elif line.strip():
                    current = None
            return blocks
        for guide in sorted((ROOT / "scripts/guides").glob("*.txt")):
            source = guide.read_text()
            for step, section in enumerate(re.split(r"^@@ \d+ .*\n", source, flags=re.M)[1:], 1):
                for level in ("hint", "investigation"):
                    text = re.split(r"^@@ \w+\n", section.split(f"@@ {level}\n")[1], flags=re.M)[0]
                    blocks = probe_blocks(text)
                    if "pacific" not in blocks and not ("lagoon" in blocks and "Pacific" in text):
                        continue
                    with self.subTest(scenario=guide.stem, step=step, level=level):
                        self.assertEqual(blocks.get("lagoon"), blocks.get("pacific"))

    def test_prose_fits_the_terminal(self):
        # Commands and data may be long. Prose and lead-ins wrap at 80 columns.
        literal = re.compile(r"^(make|show|info|ip|ping|dig|curl|gnmic|traceroute|tracepath|mtr|tail|rate|"
                             r"getent|ssh|set|delete|GROUP|TOKEN|jq|enter|commit|diff|date|cat|  )")
        for scenario in ("networking", "operations", "monitoring"):
            for level in ("task", "hint", "solution"):
                for line in self.render(scenario, "all", level).stdout.splitlines():
                    if not literal.match(line):
                        with self.subTest(scenario=scenario, level=level, line=line):
                            self.assertLessEqual(len(line), 80)

    def test_entry_is_short_and_hints_offer_commands_without_results(self):
        for scenario in ("networking", "operations", "monitoring"):
            task = self.render(scenario, 1).stdout
            # Task, commands per device, logins and places to look fit one terminal screen.
            self.assertLessEqual(len(task.splitlines()), 36)
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
        self.assertIn("make task SCENARIO=operations STEP=4", output)
        self.assertNotIn("make solution SCENARIO=operations STEP=4", output)
        self.assertNotIn("Worked answer: make solution", output)

    def test_networking_traces_both_address_families_from_both_probes(self):
        expected = (
            "traceroute -n -4 -w 1 -q 1 -m 8 198.51.100.10",
            "traceroute -n -6 -w 1 -q 1 -m 8 2001:db8:100::10",
        )
        for level in ("hint", "solution"):
            output = self.render("networking", 1, level).stdout
            for command in expected:
                with self.subTest(level=level, command=command):
                    self.assertEqual(output.count(command), 2)

    def test_networking_route_investigation_covers_both_address_families(self):
        route_commands = (
            "show network-instance default protocols bgp routes ipv4 prefix 198.51.100.0/24",
            "show network-instance default protocols bgp routes ipv6 prefix 2001:db8:100::/48",
            "show network-instance default route-table ipv4-unicast prefix 198.51.100.0/24",
            "show network-instance default route-table ipv6-unicast prefix 2001:db8:100::/48",
            "show network-instance default route-table ipv4-unicast prefix 203.0.113.0/25",
            "show network-instance default route-table ipv4-unicast prefix 203.0.113.128/25",
            "show network-instance default route-table ipv6-unicast prefix 2001:db8:a::/64",
            "show network-instance default route-table ipv6-unicast prefix 2001:db8:b::/64",
        )
        for level in ("hint", "solution"):
            output = self.render("networking", "all", level).stdout
            for command in route_commands:
                with self.subTest(level=level, command=command):
                    self.assertIn(command, output)

    def test_solution_defaults_to_one_step(self):
        result = subprocess.run(
            ["make", "--no-print-directory", "solution", "SCENARIO=networking"],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
            env=dict(os.environ, AI5049_COLOR="never"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 Test the service from both probes", result.stdout)
        self.assertNotIn("2 Resolve the name and fetch the service", result.stdout)
        self.assertIn("Worked answer", result.stdout)
        self.assertIn("make enter NODE=probe01.bob1.lagoontransit.test", result.stdout)
        self.assertIn("Investigation commands", result.stdout)
        self.assertIn(
            "BOB1 / NETWORKING / SOLUTION\n--------------------------------------------------------------------\n"
            "1 Test the service from both probes",
            result.stdout,
        )

    def test_removed_operations_steps_are_rejected_without_remapping(self):
        for step in (9, 10):
            with self.subTest(step=step):
                result = self.render("operations", step, "solution")
                self.assertEqual(result.returncode, 2)
                self.assertIn("Choose STEP=1 through STEP=8", result.stderr)
                self.assertNotIn("4 Inspect the export policy", result.stdout)
                self.assertNotIn("8 Verify the API repair", result.stdout)

    def test_student_incident_guide_does_not_give_away_the_repair(self):
        for scenario in ("operations",):
            output = self.render(scenario, "all").stdout
            for spoiler in ("BLOCK-CUSTOMER-V4", "commit now", "set --delete", "delete / network-instance"):
                self.assertNotIn(spoiler, output)
            self.assertIn("BLOCK-CUSTOMER-V4", self.render(scenario, "all", "solution").stdout)

    def test_invalid_requests_fail(self):
        for args in (("unknown", 1), ("operations", 0), ("operations", 99),
                     ("operations", "../x"), ("operations", 1, "unknown")):
            self.assertEqual(self.render(*args).returncode, 2)

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
        for scenario in ("networking", "operations", "monitoring"):
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
                                "Commands and expected results:", "Device names, logins and web UIs:",
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
            "\x1b[36m\x1b[1m→\x1b[0m When ready: \x1b[33m\x1b[1mmake task SCENARIO=operations STEP=2\x1b[0m",
            result.stdout,
        )
        plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
        next_line = next(line for line in plain.splitlines() if "When ready:" in line)
        self.assertTrue(next_line.startswith("→ When ready:"), next_line)
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
            ["bash", "scripts/next-steps.sh", "operations", "7", "solution"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="never"),
        )
        self.assertIn("\ndiff\n\nAfter confirming the original attachment is restored:\ncommit now\n", result.stdout)
        self.assertNotIn("\x1b[90mAfter confirming", result.stdout)
        self.assertIn("\nWorked answer\nBefore the change", result.stdout)

    def test_soft_wrapped_prose_and_section_transitions_render_as_paragraphs(self):
        operations = self.render("operations", 2, "solution").stdout
        self.assertIn(
            "A down peer needs adjacency diagnosis before route-policy analysis. "
            "If links and peers are up, continue to the prefix trace.",
            normalized(operations),
        )
        self.assertIn(
            "If the name does not resolve, check that the prompt shows operations01: router SSH belongs there.",
            normalized(operations),
        )
        networking = self.render("networking", "all", "hint").stdout
        self.assertIn(
            "continues to the last hop affects the service.\n\n"
            "2 Check DNS, HTTP and router access",
            networking,
        )
        monitoring = self.render("monitoring", 6, "hint").stdout
        self.assertIn(
            "Use Add query for the second expression, also in Code mode.",
            normalized(monitoring),
        )

    def test_command_lead_ins_are_petrol_headings(self):
        result = subprocess.run(
            ["bash", "scripts/next-steps.sh", "operations", "7", "solution"],
            cwd=ROOT, capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="always"),
        )
        self.assertIn(
            "\x1b[36m\x1b[1mAfter confirming the original attachment is restored:\x1b[0m\n\x1b[35mcommit now\x1b[0m",
            result.stdout,
        )

    def test_wrapping_does_not_turn_prose_into_a_terminal_context(self):
        paragraph = (
            "An established session shows that two routers can exchange routing messages. "
            "Inside a packet, the destination address still determines the route lookup."
        )
        result = subprocess.run(
            ["bash", "-c", "source scripts/ui.sh; awk -f scripts/reflow-guide.awk | ui_guide"],
            cwd=ROOT, input=paragraph + "\n", capture_output=True, text=True, check=True,
            env=dict(os.environ, AI5049_COLOR="always"),
        )
        self.assertIn("\nInside a packet", result.stdout)
        self.assertNotIn("\n\n", result.stdout)
        self.assertNotIn("\x1b[", result.stdout)
        self.assertNotIn("\034", result.stdout)
        self.assertEqual(normalized(result.stdout), paragraph)

    def test_monitoring_hint_preserves_injected_fault_until_observation(self):
        output = self.render("monitoring", 5, "hint").stdout
        commands = [line for line in output.splitlines() if line.startswith("make ")]
        self.assertNotIn("make healthy", commands)
        self.assertLess(commands.index("make test"), commands.index("make clear-routing"))
        self.assertIn("make test", commands[commands.index("make clear-routing") + 1:])

    def test_color_changes_presentation_only(self):
        for scenario in ("networking", "operations", "monitoring"):
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
