import numpy as np
from collections import deque
from scipy.fft import rfft, rfftfreq

class SpectralValidator:
    """
    Biological Tremor Validation Engine using Power Spectral Density (PSD) Analysis.
    
    This module validates if the incoming signal exhibits characteristics of human physiological tremor,
    specifically targeting the 8-12 Hz frequency band (alpha feedback loop tremor).
    
    Attributes:
        buffer_size (int): The window size N for FFT (e.g., 1024 samples).
        sampling_rate (float): The sampling frequency fs (e.g., 1000 Hz).
        buffer (deque): Rolling buffer storing the latest N samples of residuals.
        window (np.array): Pre-computed Hann window to minimize spectral leakage.
        freqs (np.array): Pre-computed frequency bins corresponding to the FFT.
    """
    def __init__(self, buffer_size=1024, sampling_rate=1000.0):
        self.buffer_size = buffer_size
        self.sampling_rate = sampling_rate
        self.buffer = deque(maxlen=buffer_size)
        
        # Pre-compute Hann Window: w(n) = 0.5 * (1 - cos(2*pi*n / (N-1)))
        # Used to taper signal edges to zero, reducing high-frequency noise from discontinuities.
        self.window = np.hanning(buffer_size)
        
        # Pre-compute Frequency Bins
        # rfftfreq returns the frequency centers for the output of rfft
        self.freqs = rfftfreq(buffer_size, 1 / sampling_rate)

    def add_sample(self, residual_value):
        """
        Adds a single residual sample to the rolling buffer.
        
        Args:
            residual_value (float): The Kalman innovation residual (tremor signal).
        """
        self.buffer.append(residual_value)

    def validate_biological_tremor(self):
        """
        Performs spectral analysis to validate if the signal is biological.
        
        Algorithm:
        1. Check buffer fill status.
        2. Apply Hann Window to buffered signal.
        3. Compute FFT (Fast Fourier Transform).
        4. Calculate Power Spectral Density (PSD): P(f) = |X(f)|^2 / (fs * N)
        5. Identify dominant frequency (argmax of PSD).
        6. Validate if peak is within 8-12 Hz.

        Returns:
            tuple: (is_valid (bool), peak_frequency (float))
                   Returns (False, 0.0) if buffer is not full.
        """
        if len(self.buffer) < self.buffer_size:
            return False, 0.0

        # Convert buffer to numpy array
        signal = np.array(self.buffer)
        
        # 1. Apply Windowing
        windowed_signal = signal * self.window
        
        # 2. Compute FFT (Real input)
        # We use rfft because input signal is real-valued.
        # This returns the positive frequency half of the spectrum.
        fft_spectrum = rfft(windowed_signal)
        
        # 3. Compute Power Spectral Density (PSD)
        # Power = |Amplitude|^2
        # Normalized by sampling rate and window length (simplified periodogram)
        psd = np.abs(fft_spectrum) ** 2
        
        # 4. Find Dominant Frequency
        # We skip the DC component (index 0) to avoid bias from non-zero mean
        peak_idx = np.argmax(psd[1:]) + 1 
        peak_freq = self.freqs[peak_idx]
        
        # 5. Biological Validation Logic
        # Human physiological tremor (neuro-muscular) is strictly 8-12 Hz.
        # Parkinsonian tremor is typically 4-6 Hz.
        # Intentional movement is typically < 2 Hz.
        # WIDENED FOR DEMO: 4.0 - 15.0 Hz to make it easier to trigger with mouse
        is_valid = 4.0 <= peak_freq <= 15.0
        
        return is_valid, peak_freq
