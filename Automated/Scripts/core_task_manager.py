import multiprocessing
import psutil
import os
import time
import json
from alert_processor import AlertProcessor

class CoreTaskManager:
    def __init__(self, max_cores=8):
        """
        Initializes the CoreTaskManager with core management logic.
        :param max_cores: Maximum number of cores to use.
        """
        self.core_states = {i: None for i in range(max_cores)}  # Track core states

    def set_core_affinity(self, process, core_id):
        """
        Set core affinity for a process.
        :param process: The process to assign.
        :param core_id: The core ID to assign the process to.
        """
        ps_process = psutil.Process(process.pid)
        ps_process.cpu_affinity([core_id])  # Restrict to a single core

    @staticmethod
    def worker(alert_name, metadata, core_id):
        """
        Worker function to process an alert.
        :param alert_name: The name of the alert being processed.
        :param metadata: The metadata for the alert.
        :param core_id: The core the task is assigned to.
        """
        print(f"Processing alert '{alert_name}' on core {core_id} (Process ID: {os.getpid()})")
        processor = AlertProcessor()
        triggered_alert = {alert_name: metadata}
        processor.process_alert(triggered_alert)
        print(f"Alert '{alert_name}' completed on core {core_id}")

    def run_alerts(self, alerts):
        """
        Run alerts with core assignment and management.
        :param alerts: Dictionary of alerts with metadata.
        """
        for alert_name, metadata in alerts.items():
            while True:
                # Check for free cores
                for core_id, process in self.core_states.items():
                    if process is None or not process.is_alive():
                        # If the core is free, start a new process
                        p = multiprocessing.Process(target=self.worker, args=(alert_name, metadata, core_id))
                        print(f"Starting process for {alert_name} on core {core_id}")
                        p.start()
                        self.set_core_affinity(p, core_id)
                        self.core_states[core_id] = p
                        break
                else:
                    # No cores are free, wait for one to become available
                    time.sleep(1)
                    continue
                break

        # Ensure all tasks are completed
        for core_id, process in self.core_states.items():
            if process:
                process.join()

        print("✅ All alerts processed.")

