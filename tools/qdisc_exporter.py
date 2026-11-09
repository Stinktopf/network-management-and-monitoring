#!/usr/bin/env python3
"""Expose actual netem egress drops in the router's root network namespace."""
import json
import logging
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def endpoints(model, source):
    node = next(key for key, value in model["nodes"].items() if value["fqdn"] == source)
    return {
        interface.replace("ethernet-1/", "e1-"): (interface, link_id)
        for link_id, link in model["links"].items()
        if link["capacity_kbps"] is not None
        for endpoint, interface in (link["a"], link["z"])
        if endpoint == node
    }


def metrics(qdiscs, ports, source):
    lines = [
        "# HELP reefnet_qdisc_dropped_packets_total Packets dropped by a Linux netem egress queue.",
        "# TYPE reefnet_qdisc_dropped_packets_total counter",
        "# HELP reefnet_qdisc_present Expected capacity queue is present (1) or missing (0).",
        "# TYPE reefnet_qdisc_present gauge",
    ]
    for device, (interface, link_id) in ports.items():
        labels = f'source={json.dumps(source)},interface_name={json.dumps(interface)},link_id={json.dumps(link_id)}'
        queues = [q for q in qdiscs if q.get("dev") == device and q.get("kind") == "netem" and q.get("root")]
        lines.append(f"reefnet_qdisc_present{{{labels}}} {int(len(queues) == 1)}")
        # Never turn absent queues or malformed samples into zero loss.
        if len(queues) == 1:
            drops = queues[0]["drops"]
            if not isinstance(drops, int) or drops < 0:
                raise ValueError("Invalid netem drop counter")
            lines.append(f"reefnet_qdisc_dropped_packets_total{{{labels}}} {drops}")
    return "\n".join(lines) + "\n"


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    source = socket.gethostname()
    logging.info("Starting queue exporter: hostname=%s", source)
    model = json.loads(Path(__file__).with_name("bob1_model.json").read_text())
    ports = endpoints(model, source)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/metrics":
                self.send_error(404)
                return
            try:
                result = subprocess.run(
                    # HTTP lives in srbase-mgmt; netem lives with container PID 1.
                    ["nsenter", "--target", "1", "--net", "/usr/sbin/tc", "-j", "-s", "qdisc", "show"],
                    capture_output=True, text=True, check=True, timeout=2,
                )
                body = metrics(json.loads(result.stdout), ports, source).encode()
            except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
                self.log_error("Collection failed: %s", error)
                if getattr(error, "stderr", None):
                    self.log_error("Collector stderr: %s", error.stderr)
                self.send_error(503, "Queue collection failed")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_request(self, *args):
            pass

    server = HTTPServer(("0.0.0.0", 9101), Handler)
    logging.info("Listening on port 9101: expected capacity interfaces=%s", ", ".join(sorted(ports)))
    server.serve_forever()


if __name__ == "__main__":
    main()
