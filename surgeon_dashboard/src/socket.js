class SocketManager {
    constructor(url = "ws://localhost:8000/ws/dashboard") {
        this.url = url;
        this.socket = null;
        this.callbacks = new Set(); // Use Set to avoid duplicates
        this.reconnectTimer = null;
        this.isExplicitlyDisconnected = false;
    }

    connect() {
        if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this.isExplicitlyDisconnected = false;
        console.log(`[Socket] Connecting to ${this.url}...`);
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            console.log("[Socket] Connected.");
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.callbacks.forEach(cb => cb(data));
            } catch (e) {
                console.error("[Socket] Parse error:", e);
            }
        };

        this.socket.onclose = (event) => {
            if (this.isExplicitlyDisconnected) return;

            console.warn("[Socket] Closed. Reconnecting in 3s...", event.reason);
            this.active = false;
            // Clear old socket ref
            this.socket = null;

            // Reconnect logic
            if (!this.reconnectTimer) {
                this.reconnectTimer = setTimeout(() => this.connect(), 3000);
            }
        };

        this.socket.onerror = (error) => {
            console.error("[Socket] Error:", error);
            this.socket.close(); // Trigger onclose
        };
    }

    subscribe(callback) {
        this.callbacks.add(callback);
        return () => this.callbacks.delete(callback); // Return unsubscribe function
    }

    disconnect() {
        this.isExplicitlyDisconnected = true;
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}

// Export singleton
export const socket = new SocketManager();
