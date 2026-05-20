import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI.
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        console.error("Uncaught error:", error, errorInfo);
        this.setState({ error, errorInfo });
    }

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div className="min-h-screen bg-black text-white flex items-center justify-center p-8 font-mono">
                    <div className="max-w-2xl w-full bg-gray-900 border border-red-600 rounded-lg p-8 shadow-[0_0_50px_rgba(220,38,38,0.5)]">
                        <div className="flex items-center mb-6">
                            <div className="text-5xl mr-4">⚠️</div>
                            <div>
                                <h1 className="text-3xl font-bold text-red-500 tracking-wider">SYSTEM FAILURE</h1>
                                <p className="text-gray-400 uppercase tracking-widest text-sm mt-1">Critical Runtime Exception</p>
                            </div>
                        </div>

                        <div className="bg-black/50 p-4 rounded border border-red-900/30 mb-6 overflow-auto max-h-64">
                            <code className="text-red-400 text-sm whitespace-pre-wrap">
                                {this.state.error && this.state.error.toString()}
                            </code>
                            {this.state.errorInfo && (
                                <pre className="text-gray-500 text-xs mt-4 overflow-x-auto">
                                    {this.state.errorInfo.componentStack}
                                </pre>
                            )}
                        </div>

                        <button
                            onClick={() => window.location.reload()}
                            className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded transition-all duration-300 w-full uppercase tracking-widest shadow-lg hover:shadow-red-600/40"
                        >
                            System Reboot
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
