#!/usr/bin/env python3
"""Run startup readiness without host Python and with controlled telemetry."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("wait-observability.sh").resolve()


class Readiness(unittest.TestCase):
    def run_check(self, response, curl_status=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commands = {
                "python3": 'touch "$HOST_PYTHON_CALLED"\nexit 127',
                "docker": '''
if [[ $1 == inspect ]]; then echo running
elif [[ $1 == exec && $2 == -i && $3 == clab-ai5049-ops01 && $4 == python3 ]]; then
  shift 4
  exec "$CONTAINER_PYTHON" "$@"
elif [[ $1 == exec && $2 == clab-ai5049-ops01 && $3 == curl ]]; then exit 0
else exit 99
fi''',
                "curl": '''
case "${*: -1}" in
  */api/v1/query) printf '%s' "$RESPONSE"; exit "$CURL_STATUS" ;;
  */api/v1/targets) echo '{"target":"clab-ai5049-gnmic:9804","health":"up"}' ;;
esac''',
                # Stop after the first unsuccessful poll instead of waiting 120 polls.
                "sleep": "exit 90",
            }
            for name, body in commands.items():
                path = root / name
                path.write_text("#!/bin/bash\n" + body + "\n")
                path.chmod(0o755)
            env = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                       CONTAINER_PYTHON=sys.executable, RESPONSE=response,
                       CURL_STATUS=str(curl_status), HOST_PYTHON_CALLED=str(root / "host-python-called"))
            result = subprocess.run(["bash", str(SCRIPT)], cwd=root, env=env,
                                    capture_output=True, text=True, timeout=5)
            self.assertFalse((root / "host-python-called").exists())
            return result, (root / ".state/queue-readiness.log").read_text()

    def test_ready_without_host_python(self):
        result, log = self.run_check(json.dumps({"data": {"result": [{}]}}))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Capacity queue collection", result.stdout)
        self.assertIn('"result": [{}]', log)

    def test_missing_queues_and_bad_responses_do_not_pass(self):
        for response in ('{"data":{"result":[]}}', 'invalid JSON', '{"status":"error"}'):
            with self.subTest(response=response):
                result, log = self.run_check(response)
                self.assertEqual(result.returncode, 90, result.stdout + result.stderr)
                self.assertIn("waiting for: Capacity queue collection", result.stdout)
                self.assertIn("Queue readiness", log)

    def test_http_failure_does_not_pass_even_with_valid_body(self):
        result, _ = self.run_check('{"data":{"result":[{}]}}', curl_status=22)
        self.assertEqual(result.returncode, 90, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
