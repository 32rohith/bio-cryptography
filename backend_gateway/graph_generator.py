import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.fft import rfft, rfftfreq

# ==========================================
# 1. IEEE STRICT FORMATTING STANDARDS
# ==========================================
# IEEE requires serif fonts, high contrast, and 300 DPI minimum.
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10,
    'figure.dpi': 300,        # Mandatory for publication
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'   # Removes wasted white space
})

# ==========================================
# 2. DATA GENERATION
# ==========================================
print("Generating 1 second of mock data at 1000Hz...")
np.random.seed(42)
time_ms = np.linspace(0, 1000, 1000) # 0 to 1000 ms

# Smooth 'Intent' wave (low frequency macroscopic movement)
filtered_intent = np.sin(2 * np.pi * 1.5 * (time_ms/1000)) * 50

# Chaotic 'Tremor' wave (9.5Hz biological physiological tremor)
valid_tremor = np.sin(2 * np.pi * 9.5 * (time_ms/1000)) * 2

# Gaussian noise
noise = np.random.normal(0, 0.5, 1000)

# Combine into Raw Input
raw_input = filtered_intent + valid_tremor + noise

# Extracted residual is exactly raw_input - filtered_intent
extracted_residual = raw_input - filtered_intent

# Generate Hack/Spoof Data (50 Hz Motor Noise)
attack_tremor = np.sin(2 * np.pi * 50 * (time_ms/1000)) * 5 
attack_residual = attack_tremor + np.random.normal(0, 0.2, len(time_ms))


# ==========================================
# 3. FIGURE 1: SIGNAL DECOMPOSITION (TIME DOMAIN)
# ==========================================
print("Generating Figure 1: Signal Decomposition...")
fig1, ax1 = plt.subplots(figsize=(8, 4))

ax1.plot(time_ms, raw_input, color='lightgray', linestyle='-', label='Raw Kinematic Input')
ax1.plot(time_ms, filtered_intent, color='black', linestyle='--', linewidth=1.5, label='Kalman Filtered Intent')

# Offset the residual by 50 units downward
ax1.plot(time_ms, extracted_residual - 50, color='dimgray', linestyle=':', label='Isolated Tremor Residual (Offset)')

ax1.set_title('Time-Domain Kinematic Signal Decomposition')
ax1.set_xlabel('Time (ms)')
ax1.set_ylabel('Displacement')
ax1.set_xlim(0, 1000)
# Expand Y-axis to prevent lines from overlapping the upper-right legend
ax1.set_ylim(-80, 120)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle=':', alpha=0.6)

fig1.savefig('fig_decomposition.png')


# ==========================================
# 4. FIGURE 2: SPECTRAL PSD
# ==========================================
print("Generating Figure 2: Spectral PSD...")
fig2, ax2 = plt.subplots(figsize=(8, 4))

# CRITICAL FIX: Subtract mean to remove 0Hz DC offset spike
centered_valid = extracted_residual - np.mean(extracted_residual)
centered_attack = attack_residual - np.mean(attack_residual)

# Apply Hann window to prevent spectral leakage
window = np.hanning(len(time_ms))
freqs = rfftfreq(len(time_ms), 1/1000) # 1000Hz sample rate

# Calculate Power Spectral Density (using rFFT) and absolute squared magnitude
valid_psd = np.abs(rfft(centered_valid * window))**2
attack_psd = np.abs(rfft(centered_attack * window))**2

# Normalize the PSD for the plot
valid_psd_norm = valid_psd / np.max(valid_psd)
attack_psd_norm = attack_psd / np.max(attack_psd)

# Plot Valid Tremor (Black, Solid)
ax2.plot(freqs, valid_psd_norm, color='black', linestyle='-', label='Valid Biological Tremor (9.5 Hz Peak)')

# Plot Attack Spoofing (Dark Gray/Red, Dashed)
ax2.plot(freqs, attack_psd_norm, color='dimgray', linestyle='--', label='Synthetic Spoofing Attack (50 Hz Peak)')

# The Highlight (8 to 12 Hz vertical band)
ax2.axvspan(8, 12, color='lightgray', alpha=0.5, label='Physiological Validation Threshold')

ax2.set_title('Spectral Power Density (PSD) Spectrogram Validation')
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Normalized Power')

# X-axis exactly 0 to 60 as requested
ax2.set_xlim(0, 60)
# Expand Y-axis to prevent lines from overlapping the upper-right legend
ax2.set_ylim(0, 1.5)

ax2.legend(loc='upper right')
ax2.grid(True, linestyle=':', alpha=0.6)

fig2.savefig('fig_spectral_validation.png')


# ==========================================
# 5. FIGURE 3: LATENCY CDF
# ==========================================
print("Generating Figure 3: Latency CDF...")
fig3, ax3 = plt.subplots(figsize=(8, 4))

# Generate array of 1,000 latency floats (normal distribution: mean 0.40, stdev 0.05)
latency_data = np.random.normal(0.40, 0.05, 1000)

# Sort data for CDF
sorted_latency = np.sort(latency_data)

# Calculate cumulative probability (Y-axis 0.0 to 1.0)
y_prob = np.arange(1, len(sorted_latency) + 1) / len(sorted_latency)

# Ensure the plot shows context out to the 2.0ms safety line clearly
ax3.set_xlim(0, 2.5)

# Plot the CDF curve in solid black
ax3.plot(sorted_latency, y_prob, color='black', linestyle='-', label='AES-GCM Decryption Pipeline')

# Draw the requested vertical dashed line at X = 2.0 ms
# Using plot instead of axvline so the line stops at Y=1.0 and doesn't shoot through the legend
ax3.plot([2.0, 2.0], [0, 1.0], color='dimgray', linestyle='--', label='Real-Time Telemetry Safety Limit (2.0 ms)')

ax3.set_title('Cumulative Distribution Function (CDF) of Cryptographic Latency')
ax3.set_xlabel('Processing Latency (ms)')
ax3.set_ylabel('Cumulative Probability (P)')

# Expand Y-axis to prevent lines from overlapping the upper-right legend
ax3.set_ylim(0, 1.35)
ax3.legend(loc='upper right')
ax3.grid(True, linestyle=':', alpha=0.6)

fig3.savefig('fig_latency_cdf.png')

print("Success! All 3 IEEE-ready figures have been correctly mathematically generated.")
