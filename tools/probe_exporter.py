#!/usr/bin/env python3
"""Active-probe exporter for the BOB1 monitoring lab."""
import argparse
import concurrent.futures
import http.server
import os
import subprocess
import threading
import time
SERVICE_V4 = "198.51.100.10"
SERVICE_V6 = "2001:db8:100::10"
SERVICE_NAME = "data.oceanresearch.test"

LOCK = threading.Lock()
RESULTS: dict[tuple[str, str], tuple[float, float, float]] = {}


def run(cmd: list[str], timeout: float = 1.5) -> tuple[float, float]:
    start = time.monotonic()
    try:
        cp = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            timeout=timeout, check=False)
        ok = 1.0 if cp.returncode == 0 else 0.0
    except (subprocess.TimeoutExpired, OSError):
        ok = 0.0
    return ok, time.monotonic() - start


def probe(kind: str, af: str) -> tuple[float, float]:
    if kind == "icmp":
        target = SERVICE_V4 if af == "ipv4" else SERVICE_V6
        return run(["ping", "-4" if af == "ipv4" else "-6", "-c", "1", "-W", "1", target])
    if kind == "dns":
        server = SERVICE_V4 if af == "ipv4" else SERVICE_V6
        qtype = "A" if af == "ipv4" else "AAAA"
        return run(["dig", f"@{server}", SERVICE_NAME, qtype, "+short", "+time=1", "+tries=1"])
    raise ValueError(kind)


def worker() -> None:
    tests = [(kind, af) for kind in ("icmp", "dns") for af in ("ipv4", "ipv6")]
    while True:
        now = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tests)) as pool:
            futs = {pool.submit(probe, k, a): (k, a) for k, a in tests}
            batch = {}
            for fut, key in futs.items():
                try:
                    ok, dur = fut.result()
                except Exception:
                    ok, dur = 0.0, 0.0
                batch[key] = (ok, dur, now)
        with LOCK:
            RESULTS.update(batch)
        time.sleep(1.0)


class Handler(http.server.BaseHTTPRequestHandler):
    source = os.environ.get("PROBE_SOURCE", "unknown")

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.path not in ("/metrics", "/"):
            self.send_response(404)
            self.end_headers()
            return
        lines = [
            "# HELP reefnet_probe_success Whether the active probe succeeded (1/0).",
            "# TYPE reefnet_probe_success gauge",
            "# HELP reefnet_probe_duration_seconds Active probe wall-clock duration.",
            "# TYPE reefnet_probe_duration_seconds gauge",
            "# HELP reefnet_probe_last_run_timestamp_seconds Unix timestamp of the last probe run.",
            "# TYPE reefnet_probe_last_run_timestamp_seconds gauge",
        ]
        with LOCK:
            items = list(RESULTS.items())
        for (kind, af), (ok, dur, ts) in sorted(items):
            labels = f'source="{self.source}",probe="{kind}",af="{af}",target="{SERVICE_NAME}"'
            lines.append(f"reefnet_probe_success{{{labels}}} {ok:.0f}")
            lines.append(f"reefnet_probe_duration_seconds{{{labels}}} {dur:.6f}")
            lines.append(f"reefnet_probe_last_run_timestamp_seconds{{{labels}}} {ts:.3f}")
        payload = ("\n".join(lines) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=9100)
    ap.add_argument("--source", required=True)
    args = ap.parse_args()
    os.environ["PROBE_SOURCE"] = args.source
    Handler.source = args.source
    threading.Thread(target=worker, daemon=True).start()
    http.server.ThreadingHTTPServer((args.listen, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
