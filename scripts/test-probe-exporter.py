#!/usr/bin/env python3
"""Probe results must represent the service response, not just a tool exit code."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('probe_exporter', Path(__file__).resolve().parents[1] / 'tools/probe_exporter.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeTests(unittest.TestCase):
    def result(self, kind, af, output='', code=0):
        with patch.object(probe.subprocess, 'run', return_value=subprocess.CompletedProcess([], code, output)) as run:
            result = probe.probe(kind, af)[0]
            return result, run.call_args.args[0]

    def test_dns_requires_expected_answer_and_noerror(self):
        for af, qtype, address in [('ipv4', 'A', probe.SERVICE_V4), ('ipv6', 'AAAA', probe.SERVICE_V6)]:
            answer = f'{probe.SERVICE_NAME}. 60 IN {qtype} {address}\n'
            for status in ['NXDOMAIN', 'SERVFAIL', 'REFUSED']:
                self.assertEqual(self.result('dns', af, f';; status: {status},\n'+answer)[0], 0)
            self.assertEqual(self.result('dns', af, ';; status: NOERROR,\n'+answer)[0], 1)
            for invalid in ['', answer.replace(address, '192.0.2.1'), answer.replace(qtype, 'TXT'), answer.replace(probe.SERVICE_NAME, 'other.test')]:
                self.assertEqual(self.result('dns', af, ';; status: NOERROR,\n'+invalid)[0], 0)

    def test_ipv6_normalization(self):
        output = ';; status: NOERROR,\ndata.oceanresearch.test. 60 IN AAAA 2001:db8:100:0:0:0:0:10\n'
        self.assertEqual(self.result('dns', 'ipv6', output)[0], 1)

    def test_http_requires_2xx(self):
        for af in ['ipv4', 'ipv6']:
            for status in ['200', '204', '299']:
                self.assertEqual(self.result('http', af, status)[0], 1)
            for status in ['000', '301', '404', '500', '']:
                self.assertEqual(self.result('http', af, status)[0], 0)
            self.assertEqual(self.result('http', af, '200', code=7)[0], 0)

    def test_http_is_independent_of_dns_and_proxy(self):
        for af, family, address in [('ipv4', '-4', probe.SERVICE_V4), ('ipv6', '-6', '['+probe.SERVICE_V6+']')]:
            _, cmd = self.result('http', af, '200')
            self.assertIn(family, cmd)
            self.assertEqual(cmd[cmd.index('--resolve')+1], f'{probe.SERVICE_NAME}:80:{address}')
            self.assertEqual(cmd[cmd.index('--noproxy')+1], '*')

    def test_process_failures(self):
        for kind in ['icmp', 'dns', 'http']:
            for error in [subprocess.TimeoutExpired('command', 1), FileNotFoundError()]:
                with patch.object(probe.subprocess, 'run', side_effect=error):
                    self.assertEqual(probe.probe(kind, 'ipv4')[0], 0)


if __name__ == '__main__':
    unittest.main()
