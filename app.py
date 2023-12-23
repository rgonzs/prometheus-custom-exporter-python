"""Application exporter"""

import os
import time
from prometheus_client import start_http_server, Gauge, Enum
# import requests

class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, app_port=80, polling_interval_seconds=5):
        self.app_port = app_port
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.current_requests = Gauge("app_requests_current", "Current requests")
        self.pending_requests = Gauge("app_requests_pending", "Pending requests")
        self.file_detection = Gauge("file_exists","File exists",['filename','hostname'])
        self.total_uptime = Gauge("app_uptime", "Uptime")
        self.health = Enum("app_health", "Health", states=["healthy", "unhealthy"])

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.check_files()
            time.sleep(self.polling_interval_seconds)

    def check_files(self):
        file = '/Users/rgonzs/typeractive_case.stl'
        cmd = os.popen("ls -l %s | awk '{ print $9 }'" % file,'r',1)
        hostname = os.popen("hostname").read().strip()
        metric = cmd.read().strip()
        if metric:
            self.file_detection.labels(file, hostname).set(1)
        else:
            self.file_detection.labels(file, hostname).set(0)

def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "5"))
    app_port = int(os.getenv("APP_PORT", "80"))
    exporter_port = int(os.getenv("EXPORTER_PORT", "9000"))

    app_metrics = AppMetrics(
        app_port=app_port,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()