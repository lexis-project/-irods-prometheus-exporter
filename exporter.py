"""Application exporter"""

import os
import time
from prometheus_client import start_http_server, Gauge
import requests
import socket
class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, app_host = "localhost", app_port=1247, polling_interval_seconds=5):
        self.app_host = app_host
        self.app_port = app_port
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.irods_service_running = Gauge("irods_service_running", "The iRODS service is currently running (1) or not (0)")

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """
        # Fetch raw status data from the application
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.app_host, self.app_port))
        totalsent = 0
        mes = "\x00\x00\x00\x33<MsgHeader_PI><type>HEARTBEAT</type></MsgHeader_PI>".encode()
        while totalsent < len(mes):
          sent = s.send(mes[totalsent:])
          if sent == 0:
              # network error
              self.irods_service_running.set(0)
              return
          totalsent = totalsent + sent
        
        res="HEARTBEAT".encode()
        l=len(res)
        chunks = []
        bytes_recd = 0
        while bytes_recd < l:
            chunk = s.recv(min(l - bytes_recd, 2048))
            if chunk == b'':
                #network error
                self.irods_service_running.set(0)
                return
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        
        mes=b''.join(chunks)
        if mes != res:
          #wrong response
          self.irods_service_running.set(0)
          return

        self.irods_service_running.set(1)
        return

def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "500"))
    app_port = 1247
    exporter_port = int(os.getenv("EXPORTER_PORT", "9856"))

    app_metrics = AppMetrics(
        app_port=app_port,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()
