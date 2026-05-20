import asyncio
import websockets
import json
import sys
import os
import time

# Add backend_gateway to path so we can import the shared crypto module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'backend_gateway')
sys.path.append(backend_path)

from core.payload_encryptor import AESGCMCipher

GATEWAY_URI = "ws://localhost:8000/ws/robot"

# ANSI Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

class RobotArmNode:
    def __init__(self):
        print(f"{BOLD}{CYAN}[SYSTEM] Initializing Surgical Robot Arm Node...{RESET}")
        print(f"{CYAN}[NETWORK] Target Gateway: {GATEWAY_URI}{RESET}")
        print(f"{BOLD}[INFO] This node visualizes the End-to-End Encryption flow:{RESET}")
        print(f"       1. Receives {RED}Encrypted Packets{RESET} from Gateway")
        print(f"       2. Decrypts using {GREEN}Bio-Key{RESET} (AES-GCM)")
        print(f"       3. Executes Command")

    async def keepalive(self, websocket):
        while True:
            try:
                await websocket.send("ping")
                await asyncio.sleep(5)
            except:
                break

    async def connect(self):
        while True:
            try:
                async with websockets.connect(GATEWAY_URI) as websocket:
                    print(f"{GREEN}[SUCCESS] Connected to Secure Gateway.{RESET}")
                    # Run keepalive and listen concurrently
                    listener = asyncio.create_task(self.listen(websocket))
                    pinger = asyncio.create_task(self.keepalive(websocket))
                    done, pending = await asyncio.wait(
                        [listener, pinger],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in pending:
                        task.cancel()
            except (ConnectionRefusedError, websockets.exceptions.ConnectionClosed):
                print(f"{YELLOW}[WARNING] Connection lost. Retrying in 3s...{RESET}")
                await asyncio.sleep(3)

    async def listen(self, websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
                recv_time = time.time()
                
                if data.get("status") == "ENCRYPTED_STREAM":
                    encrypted_payload = data.get("payload")
                    hex_key = data.get("current_key")
                    
                    # Visual Log: Raw Ciphertext (Red)
                    # Truncate for display if too long
                    disp_payload = encrypted_payload[:60] + "..." if len(encrypted_payload) > 60 else encrypted_payload
                    print(f"\n{RED}[INCOMING] 🔒 ENCRYPTED PACKET (AES-GCM){RESET}")
                    print(f"{RED}   └── Ciphertext: {disp_payload}{RESET}")
                    
                    try:
                        # Decryption Pipeline
                        session_key = bytes.fromhex(hex_key)
                        command = AESGCMCipher.decrypt_command(session_key, encrypted_payload)
                        
                        # Calculate latency if timestamp exists
                        latency = "N/A"
                        if "timestamp" in command:
                             latency = f"{(recv_time - command['timestamp']) * 1000:.2f}ms"

                        # Visual Log: Decrypted Plaintext (Green)
                        print(f"{GREEN}[DECRYPTED] ✅ AUTHENTICATED COMMAND ({latency}){RESET}")
                        print(f"{GREEN}   └── Action: {command.get('action')} | Depth: {command.get('depth')}mm | Status: EXECUTE{RESET}")
                        print(f"{CYAN}[SECURE] AES-256 KEY ROTATED (Ephemeral Session){RESET}")
                        
                    except Exception as e:
                        # Hacker/Tamper Simulation Handling
                        print(f"{BOLD}{YELLOW}[SECURITY ALERT] ⚠️ DECRYPTION FAILED: {e}{RESET}")
                        print(f"{YELLOW}   └── Packet Request Dropped. Integrity Compromised.{RESET}")
                        
            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"{RED}[ERROR] Processing loop error: {e}{RESET}")

if __name__ == "__main__":
    node = RobotArmNode()
    try:
        asyncio.run(node.connect())
    except KeyboardInterrupt:
        print(f"\n{CYAN}[SYSTEM] Shutting down robot node.{RESET}")
