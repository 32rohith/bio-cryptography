import socket
import struct
import time
import math
import requests
import threading
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi
from scipy.interpolate import interp1d

class PhyphoxSensor:
    """
    High-frequency Phyphox IMU sensor driver.
    Uses a background thread to poll data, linearly interpolates it to strictly 1000Hz,
    and a 1000Hz main loop to filter and stream data, perfectly matching the backend's expected sampling rate.
    """
    def __init__(self, phyphox_url='http://192.168.1.100:8080', target_ip='127.0.0.1', target_port=5005, sample_rate_hz=1000):
        self.phyphox_url = phyphox_url
        self.target_ip = target_ip
        self.target_port = target_port
        
        self.sample_rate_hz = sample_rate_hz
        self.period = 1.0 / self.sample_rate_hz
        
        # UDP Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # HTTP Session for faster polling
        self.session = requests.Session()
        
        # Filter Setup (8-12 Hz Bandpass at 1000Hz sampling rate)
        self.nyq = 0.5 * sample_rate_hz
        low = 8.0 / self.nyq
        high = 12.0 / self.nyq
        self.sos = butter(4, [low, high], btype='band', output='sos')
        self.zi = sosfilt_zi(self.sos)
        
        # Shared state for interpolation buffer
        self.data_buffer = []
        self.buffer_lock = threading.Lock()
        
        self.running = True
        
        print(f"[+] Phyphox Sensor Initialized:")
        print(f"    Polling URL : {self.phyphox_url}")
        print(f"    Streaming to: {self.target_ip}:{self.target_port} at {self.sample_rate_hz}Hz")

    def _poll_phyphox_loop(self):
        """
        Background thread that continuously polls Phyphox.
        Upsamples the fetched points to exactly 1000Hz using linear interpolation.
        """
        data_received = False
        last_fetch_time = -1.0
        last_processed_point = None
        
        while self.running:
            try:
                url = f"{self.phyphox_url}/get?gyr_time&gyr_x&gyr_y&gyr_z&gyrX&gyrY&gyrZ&t"
                resp = self.session.get(url, timeout=0.5)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if 'buffer' in data:
                        b = data['buffer']
                        
                        times, x_vals, y_vals, z_vals = [], [], [], []
                        
                        # Handle different buffer naming conventions
                        if 'gyrX' in b and 'gyr_time' in b:
                            times, x_vals, y_vals, z_vals = b['gyr_time']['buffer'], b['gyrX']['buffer'], b['gyrY']['buffer'], b['gyrZ']['buffer']
                        elif 'gyr_x' in b and 'gyr_time' in b:
                            times, x_vals, y_vals, z_vals = b['gyr_time']['buffer'], b['gyr_x']['buffer'], b['gyr_y']['buffer'], b['gyr_z']['buffer']
                        elif 'gyrX' in b and 't' in b:
                            times, x_vals, y_vals, z_vals = b['t']['buffer'], b['gyrX']['buffer'], b['gyrY']['buffer'], b['gyrZ']['buffer']
                        
                        if len(times) > 0:
                            if not data_received:
                                print("[+] Successfully connected and receiving data from Phyphox!")
                                data_received = True
                                
                            new_points = []
                            for i in range(len(times)):
                                t = times[i]
                                if t > last_fetch_time:
                                    last_fetch_time = t
                                    x = x_vals[i]
                                    y = y_vals[i]
                                    z = z_vals[i]
                                    mag = math.sqrt(x*x + y*y + z*z)
                                    new_points.append((t, mag))
                                    
                            if new_points:
                                if last_processed_point is not None:
                                    pts = [last_processed_point] + new_points
                                else:
                                    pts = new_points
                                    
                                if len(pts) > 1:
                                    # Interpolate to 1000Hz
                                    duration = pts[-1][0] - pts[0][0]
                                    num_samples = int(duration * 1000)
                                    
                                    if num_samples > 0:
                                        t_arr = [p[0] for p in pts]
                                        m_arr = [p[1] for p in pts]
                                        
                                        f = interp1d(t_arr, m_arr, kind='linear')
                                        t_new = np.linspace(pts[0][0], pts[-1][0], num_samples, endpoint=False)
                                        m_new = f(t_new)
                                        
                                        with self.buffer_lock:
                                            self.data_buffer.extend(m_new.tolist())
                                            # Cap buffer size to prevent infinite memory growth (max 500 samples = 0.5s)
                                            if len(self.data_buffer) > 500:
                                                self.data_buffer = self.data_buffer[-500:]
                                                
                                last_processed_point = new_points[-1]
            except requests.exceptions.RequestException:
                pass
            except Exception as e:
                print(f"[!] Background Poll Error: {e}")
            
            # Sleep briefly to not overwhelm the phone's web server
            time.sleep(0.02)

    def stream(self):
        """
        Main loop for filtering and streaming data at strictly 1000 Hz.
        """
        print(f"[+] Sensor Active: Transmitting UDP stream...")
        
        # Start background polling thread
        poll_thread = threading.Thread(target=self._poll_phyphox_loop, daemon=True)
        poll_thread.start()
        
        last_mag = 0.0
        
        try:
            next_wake_time = time.perf_counter()
            
            while self.running:
                now = time.perf_counter()
                
                # Hybrid Sleep/Spin-Wait for Precision Timing (1000Hz)
                if now < next_wake_time:
                    remaining = next_wake_time - now
                    if remaining > 0.001:  
                        time.sleep(remaining - 0.001)
                    continue
                
                next_wake_time += self.period
                
                # 1. Grab next interpolated point from queue
                with self.buffer_lock:
                    if len(self.data_buffer) > 0:
                        mag = self.data_buffer.pop(0)
                        last_mag = mag
                    else:
                        mag = last_mag # Zero-order hold if network lags
                
                # 2. Apply Bandpass Filter (runs at 1000 Hz)
                filtered_mag_array, self.zi = sosfilt(self.sos, [mag], zi=self.zi)
                filtered_mag = filtered_mag_array[0]
                
                # 3. Pack Data: float(x), float(y), double(timestamp)
                payload = struct.pack('ffd', float(filtered_mag), 0.0, time.perf_counter())
                
                # 4. Transmit via UDP
                self.sock.sendto(payload, (self.target_ip, self.target_port))
                
        except KeyboardInterrupt:
            print("\n[!] Sensor Stopped by User.")
        finally:
            self.running = False
            self.sock.close()
            self.session.close()
            print("[-] Socket and Session Closed.")

if __name__ == "__main__":
    # IMPORTANT: Update phyphox_url to the IP provided in your Phyphox app
    # Example: 'http://192.168.1.100:8080'
    sensor = PhyphoxSensor(phyphox_url='http://192.0.0.4:8080', target_port=5005)
    sensor.stream()
