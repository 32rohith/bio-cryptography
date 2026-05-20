import React, { useEffect, useRef, useState } from 'react';

const CryptoTerminal = ({ data, isLockdown, threatType }) => {
    const [logs, setLogs] = useState([]);
    const bottomRef = useRef(null);

    // Auto-scroll
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    useEffect(() => {
        if (!data) return;

        // 1. Valid Encryption Flow
        if (data.is_valid && data.generated_key_hash !== "No Lock") {
            if (Math.random() > 0.95) {
                const timestamp = new Date().toLocaleTimeString();
                const keySnippet = data.generated_key_hash;

                const newLogs = [
                    { id: Date.now() + 1, type: 'SYSTEM', text: `Biological entropy validated. Delta: ${data.filtered_x.toFixed(4)}` },
                    { id: Date.now() + 2, type: 'CRYPTO', text: `AES-256 Key Derived: ${keySnippet}...` },
                    { id: Date.now() + 3, type: 'NETWORK', text: `Encrypted payload dispatched >> Robot` }
                ];
                setLogs(prev => [...prev, ...newLogs].slice(-50));
            }
        }
        // 2. Thread/Block Flow (Instead of silence)
        else if (isLockdown) {
            if (Math.random() > 0.95) {
                const reason = threatType === 'REPLAY_ATTACK' ? 'REPLAY_DETECTED' : 'SPOOF_DETECTED';
                const newLog = {
                    id: Date.now(),
                    type: 'BLOCKED',
                    text: `*** SECURITY BLOCK *** Signal Rejected: ${reason}`
                };
                setLogs(prev => [...prev, newLog].slice(-50));
            }
        }
    }, [data, isLockdown, threatType]);

    const getTypeStyle = (type) => {
        switch (type) {
            case 'SYSTEM': return 'text-neon-blue font-bold';
            case 'CRYPTO': return 'text-neon-green font-bold';
            case 'NETWORK': return 'text-purple-400 font-bold';
            case 'BLOCKED': return 'text-red-600 font-black';
            default: return 'text-gray-400';
        }
    };

    return (
        <div className={`w-full h-96 relative bg-black border rounded-lg shadow-2xl overflow-hidden flex flex-col font-mono text-sm transition-colors duration-200
       ${isLockdown ? 'border-red-600' : 'border-gray-800'}
    `}>

            {/* Glitch Threat Overlay */}
            {isLockdown && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
                    <div className="bg-red-600/90 text-white px-8 py-6 rounded border-2 border-white shadow-[0_0_50px_rgba(220,38,38,1)] animate-bounce text-center">
                        <h2 className="text-3xl font-black mb-2 tracking-[0.2em] font-mono glitch-text">
                            [!] CRITICAL ALERT
                        </h2>
                        <p className="text-xl font-bold font-mono">
                            {threatType === 'REPLAY_ATTACK' ? 'REPLAY ATTACK DETECTED' : 'SYNTHETIC SPOOF DETECTED'}
                        </p>
                        <p className="text-sm mt-3 border-t border-white/50 pt-2">
                            CONNECTION SEVERED // SESSION LOCKED
                        </p>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className={`px-4 py-2 flex justify-between items-center border-b ${isLockdown ? 'bg-red-950 border-red-800' : 'bg-gray-900 border-gray-800'}`}>
                <div className="flex space-x-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <div className="text-gray-500 text-xs">SECURE_UPLINK_V4.2</div>
            </div>

            {/* Body */}
            <div className="flex-1 p-4 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-700">
                {logs.length === 0 && (
                    <div className="text-gray-600 italic">&gt;&gt; Waiting for secure stream...</div>
                )}

                {logs.map((log) => (
                    <div key={log.id} className="animate-fade-in-up">
                        <span className="text-gray-600 mr-2">[{new Date().toLocaleTimeString().split(' ')[0]}]</span>
                        <span className={`mr-2 [text-shadow:0_0_5px_currentColor] ${getTypeStyle(log.type)}`}>
                            [{log.type}]
                        </span>
                        <span className="text-gray-300">{log.text}</span>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default CryptoTerminal;
