import time
import socket
import struct
from pynput.mouse import Controller

# Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 8000
SAMPLE_RATE_HZ = 1000
PERIOD = 1.0 / SAMPLE_RATE_HZ

print(f"[Driver] Starting Sensor Node...")
print(f"[Driver] Streaming mouse coordinates (binary 'ff') to {UDP_IP}:{UDP_PORT}")
print(f"[Driver] Target Sample Rate: {SAMPLE_RATE_HZ} Hz")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mouse = Controller()

def sensor_loop():
    next_wake_time = time.perf_counter()
    
    while True:
        now = time.perf_counter()
        
        # Enforce 1000Hz timing
        if now < next_wake_time:
            # Sleep a bit if we have plenty of time (e.g. > 1ms), else busy wait
            remaining = next_wake_time - now
            if remaining > 0.001:
                time.sleep(remaining - 0.001)
            continue
            
        # Update target time for next iteration
        next_wake_time += PERIOD
        
        # 1. Capture Data
        try:
            x, y = mouse.position
        except Exception:
            x, y = 0.0, 0.0
            
        # 2. Pack as Binary (float, float) -> 8 bytes
        # 'f' is 4-byte float in C (standard size). Python float is usually double.
        # Use 'ff' for two floats. 
        payload = struct.pack('ff', float(x), float(y))
        
        # 3. Stream via UDP
        sock.sendto(payload, (UDP_IP, UDP_PORT))
        
        # Optional: Print every 1000 samples to avoid flooding console
        # but User said "Add clear terminal logging so I know it's transmitting"
        # We'll log less frequently to keep performance high, or standard log
        if int(now * 10) % 10 == 0: # Log roughly once per second depending on exact timing alignment or use counter
             pass

    # Better logging approach with counter
    
if __name__ == "__main__":
    try:
        count = 0
        next_wake_time = time.perf_counter()
        
        while True:
            # Precision Timing
            now = time.perf_counter()
            while now < next_wake_time:
                now = time.perf_counter()
            
            next_wake_time += PERIOD
            
            # Logic
            x, y = mouse.position
            payload = struct.pack('ff', float(x), float(y))
            sock.sendto(payload, (UDP_IP, UDP_PORT))
            
            count += 1
            if count % 1000 == 0:
                print(f"[Driver] Transmitting: x={x:.1f}, y={y:.1f} | Rate: ~{SAMPLE_RATE_HZ}Hz")
                
    except KeyboardInterrupt:
        print("\n[Driver] Stopping...")
        sock.close()
