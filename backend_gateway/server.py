import asyncio
import json
import struct
import time
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.crypto import BioCryptoEngine
from core.kalman import AdaptiveKalmanFilter
from core.spectral import SpectralValidator

# Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
BROADCAST_RATE_HZ = 60
BROADCAST_INTERVAL = 1.0 / BROADCAST_RATE_HZ

app = FastAPI()

# ANSI Colors for flashy logs
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared State
connected_dashboard_websockets = set()
connected_arm_websockets = set()
data_queue = asyncio.Queue()

# Initialize Core Modules
# We use a single 2D Kalman Filter as per design
kalman_filter = AdaptiveKalmanFilter()
spectral_validator = SpectralValidator()
crypto_engine = BioCryptoEngine()
from core.payload_encryptor import AESGCMCipher
from core.metrics_exporter import ResearchLogger

from core.metrics_exporter import ResearchLogger

research_logger = ResearchLogger()

class ReplayDetector:
    """
    Detects Replay Attacks by checking if the incoming payload (binary)
    has been seen within the last 10 seconds.
    """
    def __init__(self, retention_sec=10):
        self.retention_sec = retention_sec
        self.history = {} # fast lookup: bytes -> timestamp

    def check(self, payload_bytes):
        now = time.time()
        
        # Cleanup old entries (simple lazy cleanup or scheduled)
        # For performance in this loop, we might just do it periodically or 
        # on every check if N is small. 10,000 items is small for python dict.
        # Let's do a quick random cleanup or just linear scan if needed, 
        # but dict comprehension is fast.
        
        # Optimization: Only cleanup every 100 checks to save CPU
        if len(self.history) > 20000:
             self.history = {k:v for k,v in self.history.items() if now - v < self.retention_sec}

        if payload_bytes in self.history:
            # Check if it is within window (though we only keep recent ones)
            last_seen = self.history[payload_bytes]
            if now - last_seen < self.retention_sec:
                return True # Replay Detected
        
        self.history[payload_bytes] = now
        return False

replay_detector = ReplayDetector(retention_sec=10)

class SensorUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.last_log_time = 0
        
    def connection_made(self, transport):
        self.transport = transport
        print(f"UDP Listener started on {UDP_IP}:{UDP_PORT}")

    def datagram_received(self, data, addr):
        try:
            # Expecting 16 bytes (float x, float y, double timestamp)
            if len(data) == 16:
                start_time = time.perf_counter() # Latency tracking
                # Unpack: x, y, packet_timestamp
                raw_x, raw_y, packet_ts = struct.unpack('ffd', data)
                
                # 0. Replay Defense
                is_replay = replay_detector.check(data)
                attack_flag = 0 
                
                if is_replay:
                    print(f"\033[94m[DEFENSE] Replay Attack Detected! dropped.\033[0m")
                    attack_flag = 2
                    # Alert Dashboard
                    alert = {"status": "THREAT_DETECTED", "reason": "REPLAY_ATTACK"}
                    # urgency: push to queue immediately or separate alert channel?
                    # sticking to data_queue but with special flag
                    data_queue.put_nowait(alert)

                else:
                    # 1. Kalman Filter (2D Prediction & Update)
                    kalman_filter.predict()
                    # Update returns residuals (innovation)
                    residuals = kalman_filter.update(raw_x, raw_y)
                    res_x, res_y = residuals[0], residuals[1]
                    
                    # Compute filtered estimate (Measurement - Residual)
                    filtered_x = raw_x - res_x
                    filtered_y = raw_y - res_y

                    # 2. Spectral Validation (Check X-axis residual for tremor)
                    spectral_validator.add_sample(res_x)
                    is_valid, peak_freq = spectral_validator.validate_biological_tremor()

                    # Defense: Drop if Spectral is Invalid (Spoofing)
                    # "If ... returns False ... immediately drop the payload."
                    # But we usually stream "is_valid=False" to dashboard to show RED graph?
                    # User requirement: "Do not pass data to the Crypto Engine."
                    # "Drop the payload" usually means don't process further. 
                    # BUT we still need to log it for academic purposes.
                    
                    if not is_valid:
                        # Check strictly if it is "Spoof" (Noise) vs "Normal Static"
                        # If peak_freq is strong but wrong freq -> Spoof (Motor)
                        # If no peak / low energy -> Static (Normal)
                        # For Red Team "Motor Noise", it generates 50Hz.
                        # Spectral will see 50Hz. 50Hz is outside 8-12Hz.
                        # So is_valid = False.
                        if peak_freq > 20.0: # Rough heuristic for "Motor Spoof" vs "Resting"
                             current_time = time.time()
                             if current_time - self.last_log_time > 1.0:
                                 print(f"\033[94m[DEFENSE] Spectral Spoof Detected ({peak_freq:.1f}Hz). Dropped.\033[0m")
                                 self.last_log_time = current_time
                             attack_flag = 1
                             data_queue.put_nowait({"status": "THREAT_DETECTED", "reason": "SPOOF_ATTACK"})
                    
                    # 3. Key Generation (Only if valid)
                    generated_key_hash = "No Lock"
                    full_key_bytes = None
                    full_hex = None
                    
                    if is_valid and attack_flag == 0:
                        # Use the full spectral buffer (1024 samples) as entropy source
                        entropy_pool = list(spectral_validator.buffer)
                        raw_entropy = crypto_engine.quantize_residuals(entropy_pool)
                        full_key_bytes, generated_key_hash = crypto_engine.derive_aes_key(raw_entropy)
                        full_hex = generated_key_hash 
                        generated_key_hash = full_hex[:8] 
                        
                        # Demo Visualization Logs
                        if time.time() % 0.5 < 1/60: # Print roughly every 0.5s to avoid spam
                            print(f"{CYAN}[MATH] Kalman Filter Active -> Innovation: {res_x:.4f}{RESET}")
                            print(f"{GREEN}[FFT] {peak_freq:.1f}Hz Peak Detected (Bio-Signal Valid){RESET}")
                            print(f"{YELLOW}[CRYPTO] Key Generated: {generated_key_hash}... (Ephemeral){RESET}") 

                    # Prepare Payload (For Dashboard Viz)
                    # Even if attack, we might want to show the graph lines? 
                    # User said "drop the payload" -> "Do not pass to Crypto Engine".
                    # But Dashboard needs raw_x/filtered_x to draw the Red line.
                    # So we will send the visualization payload, but WITHOUT key and WITH attack status.
                    
                    payload = {
                        "raw_x": float(raw_x),
                        "filtered_x": float(filtered_x),
                        "filtered_y": float(filtered_y),       
                        "tremor_freq": float(peak_freq),
                        "is_valid": bool(is_valid),     
                        "generated_key_hash": generated_key_hash,
                        "encrypted_preview": generated_key_hash,
                        "full_key_hex": full_hex
                    }
                    
                    # Add Alert if Spoof
                    if attack_flag == 1:
                        payload["status"] = "THREAT_DETECTED"
                        payload["reason"] = "SPOOF_ATTACK"

                    if attack_flag == 0:
                         data_queue.put_nowait(payload)
                
                # Log to CSV (Always Log)
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                
                # If Replay, we didn't calculate filtered/residual/freq. Usage default 0.
                if is_replay:
                     research_logger.log(
                        timestamp_ms=time.time() * 1000,
                        raw_x=raw_x, raw_y=raw_y,
                        filtered_x=0.0, filtered_y=0.0,
                        residual_x=0.0, residual_y=0.0,
                        fft_peak_freq=0.0,
                        latency_ms=latency_ms,
                        attack_flag=2
                     )
                else:
                     research_logger.log(
                        timestamp_ms=time.time() * 1000,
                        raw_x=raw_x, raw_y=raw_y,
                        filtered_x=filtered_x, filtered_y=filtered_y,
                        residual_x=res_x, residual_y=res_y,
                        fft_peak_freq=peak_freq, 
                        latency_ms=latency_ms,
                        attack_flag=attack_flag
                    )
                
                
                # Log to CSV (100Hz downsampled internally)
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                
                research_logger.log(
                    timestamp_ms=time.time() * 1000,
                    raw_x=raw_x, raw_y=raw_y,
                    filtered_x=filtered_x, filtered_y=filtered_y,
                    residual_x=res_x, residual_y=res_y,
                    fft_peak_freq=peak_freq, 
                    latency_ms=latency_ms
                )
            else:
                 print(f"[DEBUG] Packet size mismatch: Received {len(data)} bytes, expected 16. Protocol update required?")

        except Exception as e:
            print(f"[ERROR] Datagram Handler Exception: {e}")
            import traceback
            traceback.print_exc()

import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)

async def broadcast_loop():
    """
    Broadcasts the latest data at 60Hz.
    Drains the queue to get the very latest frame, dropping intermediate frames.
    """
    while True:
        await asyncio.sleep(BROADCAST_INTERVAL)
        
        if not connected_dashboard_websockets and not connected_arm_websockets:
            # Clear queue to prevent memory leak
            while not data_queue.empty():
                try:
                    data_queue.get_nowait()
                except:
                    break
            continue

        # Get latest data (drain queue)
        latest_item = None
        while not data_queue.empty():
            try:
                latest_item = data_queue.get_nowait()
            except:
                break
        
        if latest_item:
            # 2. Robot Arm Broadcast (Simulated Encrypted Command)
            # Only send if valid and NOT a threat
            is_threat = latest_item.get("status") == "THREAT_DETECTED"
            if latest_item.get("is_valid") and latest_item.get("full_key_hex") and connected_arm_websockets and not is_threat:
                try:
                    session_key = bytes.fromhex(latest_item["full_key_hex"])
                    
                    # Create a simulated command based on the filtered intention (smooth movement)
                    # Mapping filtered_x/y to normalized arm coordinates
                    command_payload = {
                        "action": "INCISION",
                        "depth": 2.5,
                        "timestamp": time.time()
                    }
                    
                    # Encrypt
                    encrypted_b64 = AESGCMCipher.encrypt_command(session_key, command_payload)
                    
                    # Packet for Robot (Simulating the network packet)
                    robot_packet = {
                        "status": "ENCRYPTED_STREAM",
                        "payload": encrypted_b64,
                        "current_key": latest_item["full_key_hex"] # Key exchange simulation
                    }
                    
                    msg = json.dumps(robot_packet, cls=NumpyEncoder)
                    to_remove_arm = set()
                    for ws in connected_arm_websockets:
                        try:
                            await ws.send_text(msg)
                        except:
                            to_remove_arm.add(ws)
                    if to_remove_arm:
                        connected_arm_websockets.difference_update(to_remove_arm)
                        
                except Exception as e:
                    print(f"Encryption Broadcast Error: {e}")

            # 3. Dashboard Broadcast (Always send visualization + alerts)
            # If it's a pure alert (just status), broadcast it.
            # If it's a payload, broadcast it.
            msg = json.dumps(latest_item, cls=NumpyEncoder)
            to_remove_dash = set()
            for ws in connected_dashboard_websockets:
                try:
                    await ws.send_text(msg)
                except:
                    to_remove_dash.add(ws)
            if to_remove_dash:
                connected_dashboard_websockets.difference_update(to_remove_dash)


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await websocket.accept()
    connected_dashboard_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_dashboard_websockets.remove(websocket)

@app.websocket("/ws/robot")
async def websocket_arm(websocket: WebSocket):
    await websocket.accept()
    connected_arm_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_arm_websockets.remove(websocket)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    
    # Start UDP Listener
    await loop.create_datagram_endpoint(
        lambda: SensorUDPProtocol(),
        local_addr=(UDP_IP, UDP_PORT)
    )
    
    # Start Broadcast Loop
    asyncio.create_task(broadcast_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
