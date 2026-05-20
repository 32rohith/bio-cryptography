import { useEffect, useState } from 'react';
import { socket } from './socket';
import LiveGraph from './components/LiveGraph';
import CryptoTerminal from './components/CryptoTerminal';

function App() {
  const [dataBuffer, setDataBuffer] = useState([]);
  const [metrics, setMetrics] = useState({
    tremor_freq: 0,
    is_valid: false,
    generated_key_hash: "Initializing...",
    status: "NORMAL",
    reason: null
  });

  useEffect(() => {
    // Socket connection handled by singleton, just sub here
    socket.connect();

    const unsubscribe = socket.subscribe((newData) => {
      setMetrics((prev) => ({
        tremor_freq: newData.tremor_freq !== undefined ? newData.tremor_freq : prev.tremor_freq,
        is_valid: newData.is_valid !== undefined ? newData.is_valid : prev.is_valid,
        generated_key_hash: newData.generated_key_hash || prev.generated_key_hash,
        status: newData.status || "NORMAL",
        reason: newData.reason || null
      }));

      // Only update graph buffer if we have coordinate data
      if (newData.raw_x !== undefined) {
        setDataBuffer((prev) => {
          const newBuffer = [...prev, {
            timestamp: Date.now(),
            raw_x: newData.raw_x,
            filtered_x: newData.filtered_x
          }];
          if (newBuffer.length > 200) return newBuffer.slice(newBuffer.length - 200);
          return newBuffer;
        });
      }
    });

    return () => unsubscribe();
  }, []);

  const isSecure = metrics.is_valid && metrics.generated_key_hash !== "No Lock";
  const isLockdown = metrics.status === "THREAT_DETECTED";
  const threat = metrics.reason;

  return (
    <div className="min-h-screen bg-medical-dark bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 to-black text-gray-200 p-8 flex flex-col font-sans">

      {/* Header */}
      <header className="flex justify-between items-end mb-8 border-b border-gray-800 pb-6">
        <div>
          <h1 className="text-3xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-neon-blue to-blue-600 font-mono">
            BIO-CRYPTOGRAPHIC <span className="text-white">INTERFACE</span>
          </h1>
          <p className="text-muted-gray text-sm mt-1 tracking-widest uppercase">
            Robotic Telesurgery Security Gateway
          </p>
        </div>

        {/* Security Badge */}
        <div className={`flex items-center px-6 py-3 rounded-lg border backdrop-blur-sm transition-all duration-500 ${isSecure
          ? 'bg-neon-green/10 border-neon-green shadow-[0_0_20px_rgba(0,255,157,0.2)]'
          : 'bg-alert-red/10 border-alert-red animate-pulse'
          }`}>
          <div className="text-3xl mr-4">{isSecure ? '🔒' : '⚠️'}</div>
          <div>
            <div className={`font-bold text-sm tracking-wider ${isSecure ? 'text-neon-green' : 'text-alert-red'}`}>
              {isSecure ? 'ZERO-TRUST SECURE' : 'SPOOF DETECTED'}
            </div>
            <div className="font-mono text-xs text-gray-400">
              {isSecure ? `SESSION_KEY: ${metrics.generated_key_hash}` : 'ACCESS DENIED'}
            </div>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1">

        {/* Left Col: Viz & Terminal */}
        <div className="lg:col-span-2 space-y-6">
          <LiveGraph data={dataBuffer} isLockdown={isLockdown} />
          <CryptoTerminal data={dataBuffer[dataBuffer.length - 1]} isLockdown={isLockdown} threatType={threat} />
        </div>

        {/* Right Col: Stats */}
        <div className="space-y-6">

          {/* Signal Quality Card */}
          <div className="bg-medical-panel/40 border border-gray-700 rounded-xl p-6 backdrop-blur">
            <h3 className="text-gray-400 text-xs font-bold uppercase tracking-widest mb-4">Tele-metrics</h3>

            <div className="flex justify-between items-center mb-4">
              <span className="text-gray-500 text-sm">Sample Rate</span>
              <span className="font-mono text-neon-blue">1000 Hz</span>
            </div>
            <div className="flex justify-between items-center mb-4">
              <span className="text-gray-500 text-sm">Latency</span>
              <span className="font-mono text-neon-green">~1.20 ms</span>
            </div>
            <div className="border-t border-gray-700 my-4"></div>

            <div className="mb-2">
              <span className="text-gray-500 text-sm">Tremor Frequency</span>
              <div className="flex items-end mt-1">
                <span className="text-3xl font-bold text-white">{metrics.tremor_freq.toFixed(1)}</span>
                <span className="text-sm text-gray-500 mb-1 ml-2">Hz</span>
              </div>
            </div>

            {/* Freq Bar */}
            <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${isSecure ? 'bg-neon-green' : 'bg-red-500'}`}
                style={{ width: `${(metrics.tremor_freq / 20) * 100}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1 flex justify-between">
              <span>0 Hz</span>
              <span>20 Hz</span>
            </div>
          </div>

          {/* Encryption Key Card */}
          <div className={`border rounded-xl p-6 transition-colors duration-300 ${isSecure ? 'bg-gray-900 border-neon-green/30' : 'bg-red-900/10 border-red-500/30'}`}>
            <h3 className="text-gray-400 text-xs font-bold uppercase tracking-widest mb-4">
              HKDF-SHA256 Entropy
            </h3>
            <div className="font-mono text-xs break-all leading-relaxed text-gray-300">
              {isSecure ? (
                <>
                  <span className="text-neon-green">-----BEGIN SESSION KEY-----</span><br />
                  {metrics.generated_key_hash}...<br />
                  <span className="text-neon-green">-----END SESSION KEY-----</span>
                </>
              ) : (
                <span className="text-red-400">WAITING FOR BIOMETRIC LOCK...</span>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;
