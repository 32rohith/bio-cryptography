import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';

const LiveGraph = ({ data, isLockdown }) => {
    return (
        <div className={`w-full h-96 backdrop-blur-md border rounded-xl p-4 shadow-lg relative overflow-hidden transition-colors duration-300
          ${isLockdown ? 'bg-black border-red-600/50 shadow-[0_0_30px_rgba(220,38,38,0.2)]' : 'bg-medical-panel/50 border-gray-700'}
        `}>
            {/* Grid Overlay Effect */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,255,157,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,157,0.03)_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none"></div>

            <div className="flex justify-between items-center mb-4 relative z-10">
                <h3 className={`font-mono text-lg tracking-widest uppercase transition-colors
                  ${isLockdown ? 'text-red-500 animate-pulse' : 'text-neon-blue'}
                `}>
                    {isLockdown ? 'SIGNAL SEVERED' : 'Signal Analysis'} <span className="text-xs text-gray-400 normal-case">/ Real-time 60Hz</span>
                </h3>
                <div className="flex space-x-4 text-xs font-mono">
                    <div className="flex items-center">
                        <div className="w-3 h-3 bg-gray-500 rounded-sm mr-2 opacity-50"></div>
                        <span className="text-gray-400">RAW_INPUT</span>
                    </div>
                    <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-2 shadow-[0_0_10px_currentColor] ${isLockdown ? 'bg-red-600 text-red-600' : 'bg-neon-blue text-neon-blue'}`}></div>
                        <span className={isLockdown ? 'text-red-500' : 'text-neon-blue'}>
                            {isLockdown ? 'THREAT_SIG' : 'FILTERED_INTENT'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="w-full h-[320px] relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                        <XAxis hide={true} domain={['auto', 'auto']} />
                        <YAxis hide={true} domain={['auto', 'auto']} />

                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#0f172a',
                                border: '1px solid #1e293b',
                                color: '#fff',
                                fontFamily: 'monospace'
                            }}
                            itemStyle={{ fontSize: '12px' }}
                        />

                        {/* Raw Input - Muted Gray */}
                        <Line
                            type="monotone"
                            dataKey="raw_x"
                            stroke="#64748b"
                            strokeWidth={2}
                            strokeOpacity={0.6}
                            dot={false}
                            isAnimationActive={false}
                        />

                        {/* Filtered Intent - Neon Blue (or Red if Lockdown) */}
                        <Line
                            type="monotone"
                            dataKey="filtered_x"
                            stroke={isLockdown ? '#ef4444' : '#00f0ff'}
                            strokeWidth={3}
                            dot={false}
                            isAnimationActive={false}
                            filter={isLockdown ? "url(#glow-red)" : "url(#glow)"}
                        />

                        {/* SVG Filter for Glow Effect */}
                        <defs>
                            <filter id="glow" height="300%" width="300%" x="-75%" y="-75%">
                                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                                <feMerge>
                                    <feMergeNode in="coloredBlur" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                            <filter id="glow-red" height="300%" width="300%" x="-75%" y="-75%">
                                <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                                <feFlood floodColor="#ef4444" result="glowColor" />
                                <feComposite in="glowColor" in2="coloredBlur" operator="in" result="coloredGlow" />
                                <feMerge>
                                    <feMergeNode in="coloredGlow" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                        </defs>

                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default LiveGraph;
