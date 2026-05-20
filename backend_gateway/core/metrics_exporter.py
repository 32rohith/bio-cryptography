import csv
import time
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ResearchLogger:
    """
    Logs sensor and processing metrics to a CSV file for academic analysis.
    Handles downsampling (1000Hz -> 100Hz) and non-blocking disk I/O.
    """
    def __init__(self, filename="results_log.csv", downsample_factor=10):
        self.filename = filename
        self.downsample_factor = downsample_factor
        self.counter = 0
        self.buffer = []
        self.buffer_size_limit = 100 # Flush every 100 records (1 second of data at 100Hz)
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Initialize CSV with header
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp_ms", 
                    "raw_x", "raw_y", 
                    "filtered_x", "filtered_y", 
                    "residual_x", "residual_y", 
                    "fft_peak_freq", 
                    "processing_latency_ms",
                    "attack_flag" # 0=Normal, 1=Spoof, 2=Replay
                ])
                print(f"[ResearchLogger] Created new log file: {self.filename}")

    def log(self, timestamp_ms, raw_x, raw_y, filtered_x, filtered_y, residual_x, residual_y, fft_peak_freq, latency_ms, attack_flag=0):
        """
        Logs a single data point. Respects downsampling factor.
        """
        self.counter += 1
        if self.counter % self.downsample_factor != 0:
            return

        # Create record
        record = [
            f"{timestamp_ms:.2f}",
            f"{raw_x:.4f}", f"{raw_y:.4f}",
            f"{filtered_x:.4f}", f"{filtered_y:.4f}",
            f"{residual_x:.4f}", f"{residual_y:.4f}",
            f"{fft_peak_freq:.2f}",
            f"{latency_ms:.2f}",
            f"{attack_flag}"
        ]
        
        self.buffer.append(record)
        
        # Auto-flush if buffer is full
        if len(self.buffer) >= self.buffer_size_limit:
            self.flush_async()

    def flush_async(self):
        """
        Triggers a non-blocking flush to disk.
        """
        if not self.buffer:
            return

        # Swap buffer to avoid race conditions (simple swap is atomic-ish enough for this single-threaded event loop usage)
        # But since we are creating a task, we should make a copy/reference.
        data_to_write = list(self.buffer)
        self.buffer = [] # Clear immediately
        
        # Offload to thread
        loop = asyncio.get_event_loop()
        loop.run_in_executor(self.executor, self._write_to_disk, data_to_write)

    def _write_to_disk(self, data):
        """
        Blocking write operation (runs in thread).
        """
        try:
            with open(self.filename, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(data)
        except Exception as e:
            print(f"[ResearchLogger] Error writing to disk: {e}")

    def close(self):
        """
        Force flush remaining data and shutdown executor.
        """
        if self.buffer:
            self._write_to_disk(self.buffer)
        self.executor.shutdown(wait=True)
