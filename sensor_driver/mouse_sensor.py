import socket
import struct
import time
from pynput.mouse import Controller

class MouseSensor:
    """
    High-frequency mouse sensor driver simulating an IMU.
    Captures X/Y coordinates and streams via UDP.
    """
    def __init__(self, target_ip='127.0.0.1', target_port=5005, sample_rate_hz=1000):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sample_rate_hz = sample_rate_hz
        self.period = 1.0 / self.sample_rate_hz
        
        # Initialize UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Initialize Mouse Controller
        self.mouse = Controller()
        
        print(f"[+] Sensor Initialized: Target {self.target_ip}:{self.target_port}")

    def stream(self):
        """
        Main loop for capturing and streaming data.
        Enforces strict timing using spin-wait hybrid approach.
        """
        print(f"[+] Sensor Active: Transmitting UDP stream at {self.sample_rate_hz}Hz...")
        
        try:
            next_wake_time = time.perf_counter()
            
            while True:
                now = time.perf_counter()
                
                # Hybrid Sleep/Spin-Wait for Precision Timing
                if now < next_wake_time:
                    remaining = next_wake_time - now
                    if remaining > 0.001:  # Sleep only if enough time remains
                        time.sleep(remaining - 0.001)
                    continue  # Poll again (spin-wait final micro-seconds)
                
                # Update next target time (drift correction)
                next_wake_time += self.period
                
                # 1. Capture Coordinates
                try:
                    # pynput returns (x, y) tuple
                    x, y = self.mouse.position 
                except Exception:
                    x, y = 0.0, 0.0
                
                # 2. Pack Data: 2 floats (4 bytes) + 1 double (8 bytes) = 16 bytes total
                # 'ffd' format: float(x), float(y), double(timestamp)
                # Using time.perf_counter() for high precision on Windows
                payload = struct.pack('ffd', float(x), float(y), time.perf_counter())
                
                # 3. Transmit via UDP
                self.sock.sendto(payload, (self.target_ip, self.target_port))
                
        except KeyboardInterrupt:
            print("\n[!] Sensor Stopped by User.")
        finally:
            self.sock.close()
            print("[-] Socket Closed.")

if __name__ == "__main__":
    # Create and start sensor
    sensor = MouseSensor(target_port=5005)
    sensor.stream()
