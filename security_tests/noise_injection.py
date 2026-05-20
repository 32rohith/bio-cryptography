import asyncio
import argparse
import struct
import time
import numpy as np
import sys

# Configuration
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5005
RATE_HZ = 1000
INTERVAL = 1.0 / RATE_HZ

# ANSI Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

class AttackClient:
    def __init__(self, mode):
        self.mode = mode
        self.transport = None
        self.t_start = time.time()
        print(f"{BOLD}{RED}[ATTACK] Initializing Synthetic Noise Injector...{RESET}")
        print(f"{RED}[CONFIG] Target: {TARGET_IP}:{TARGET_PORT} | Rate: {RATE_HZ}Hz{RESET}")
        print(f"{RED}[MODE]   Switched to: {mode.upper()}_INJECTION{RESET}")

    def generate_white_noise(self):
        """Generates chaotic, flat-spectrum random noise."""
        # Mean 0, Std Dev 5.0 (High amplitude chaos)
        x = np.random.normal(0, 5.0)
        y = np.random.normal(0, 5.0)
        return x, y

    def generate_motor_noise(self):
        """Generates a perfect 50Hz sine wave (robotic motor hum)."""
        t = time.time() - self.t_start
        # 50Hz sine wave, Amplitude 2.0
        val = 2.0 * np.sin(2 * np.pi * 50 * t)
        return val, val

    def connection_made(self, transport):
        self.transport = transport
        print(f"{BOLD}{RED}[ATTACK] ⚡ FLOODING STREAM STARTED!{RESET}")

    def datagram_received(self, data, addr):
        pass

    def error_received(self, exc):
        print(f"{YELLOW}[ERROR] {exc}{RESET}")

    def connection_lost(self, exc):
        print(f"{YELLOW}[WARN] Connection closed.{RESET}")

async def attack_loop(mode):
    loop = asyncio.get_running_loop()
    
    # Create UDP endpoint
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: AttackClient(mode),
        remote_addr=(TARGET_IP, TARGET_PORT)
    )
    
    client = protocol

    try:
        while True:
            t0 = time.perf_counter()
            
            # Generate Attack Payload
            if mode == 'white_noise':
                x, y = client.generate_white_noise()
            elif mode == 'motor':
                x, y = client.generate_motor_noise()
            else:
                x, y = 0.0, 0.0

            # Pack and Send
            # Protocol Release v2: 16 bytes (float x, float y, double timestamp)
            payload = struct.pack('ffd', float(x), float(y), time.perf_counter())
            transport.sendto(payload)

            # Precise Timing
            t1 = time.perf_counter()
            dt = t1 - t0
            sleep_time = max(0, INTERVAL - dt)
            await asyncio.sleep(sleep_time)

    except KeyboardInterrupt:
        print(f"\n{GREEN}[SYSTEM] Attack Ceased.{RESET}")
    finally:
        transport.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bio-Crypto Red Team Tool")
    parser.add_argument("--mode", choices=['white_noise', 'motor'], help="Attack simulation mode")
    
    args = parser.parse_args()
    
    mode = args.mode
    if not mode:
        print(f"{BOLD}{RED}>>> SELECT ATTACK MODE <<<{RESET}")
        print("1. White Noise (Static/Random)")
        print("2. Motor Noise (50Hz Robotic Sine Wave)")
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            mode = "white_noise"
        else:
            mode = "motor"

    try:
        asyncio.run(attack_loop(mode))
    except (KeyboardInterrupt, OSError):
        pass
