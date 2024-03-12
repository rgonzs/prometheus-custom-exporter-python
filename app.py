"""Application exporter"""

import os
import time
import yaml
import requests

from prometheus_client import start_http_server, Gauge, Enum

class PrometheusApiClient:

    def __init__(self, url:str) -> None:
        self.url = f"{url}/api/v1/query?"

    def custom_query_labels(self, query):
        res = requests.get(f'{self.url}query={query}')
        json = res.json()
        if json["status"] == "success":
            return map(self.__get_labels, json["data"]["result"])
        else:
            return []
        
    def __get_labels(self, metric):
        return metric['metric']


class Config:
    __config = yaml.safe_load(open('/config/config.yaml','r'))
    role = __config['role']
    scan_paths = __config['scan_paths']
    prometheus_url = __config['prometheus']['url'] if role == 'slave' else ""
    prometheus_ssl = __config['prometheus']['disable_ssl'] if role == 'slave' else True


class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, polling_interval_seconds=5):
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.total_uptime = Gauge("app_uptime", "Uptime")
        self.file_sha1sum = Gauge("sha1sum_file","Original File",['filename','sha1sum','hostname','original'])
        self.match_sha1sum = Gauge("sha1sum_match", "Remote File Match", ['filename','hostname'])
        self.health = Enum("app_health", "Health", states=["healthy", "unhealthy"])
        self.prom_client = PrometheusApiClient(url=Config.prometheus_url) if Config.role == 'slave' else None

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.load_shasum()
            time.sleep(self.polling_interval_seconds)
    
    def __check_item_on_dict(self, lst, filename):
        if lst['filename'] == filename:
            # print(lst['filename'])
            return lst['sha1sum']

    def load_shasum(self):
        for dir in Config.scan_paths:
            files = os.listdir(dir)
            for file in files:
                cmd = os.popen("sha1sum %s/%s | awk '{print $1}'" % (dir, file), 'r', 1)
                hostname = os.popen("hostname").read().strip()
                sha1sum = cmd.read().strip()
                if Config.role == "master":
                    if sha1sum:
                        self.file_sha1sum.labels(file, sha1sum, hostname, 1).set(1)
                    else:
                        self.file_sha1sum.labels( '', '', '', 0).set(0)
                if Config.role == "slave":
                    original = self.prom_client.custom_query_labels('sha1sum_file{original="1"}')
                    sha1sum_original = ""
                    for item in original:
                        sum = self.__check_item_on_dict(item, file)
                        if sum:
                            sha1sum_original = sum
                        
                    print({'sha1sum':sha1sum, 'sha1sum_original':sha1sum_original,'file': file})
                    match = True if sha1sum_original == sha1sum else False
                    if match:
                        self.match_sha1sum.labels(file, hostname).set(1)
                    else:
                        self.match_sha1sum.labels(file, hostname).set(0)


def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "5"))
    exporter_port = int(os.getenv("EXPORTER_PORT", "9000"))

    app_metrics = AppMetrics(
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()