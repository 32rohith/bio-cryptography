import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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
# 2. FIGURE 4: REPLAY ATTACK CONFUSION MATRIX
# ==========================================
print("Generating Figure 4: Replay Attack Confusion Matrix...")

# Confusion Matrix Data:
# 500 valid allowed (True Positives), 500 malicious blocked (True Negatives)
# 0 False Positives, 0 False Negatives
# Format: np.array([[TN, FP], [FN, TP]])
# Let's align it with standard binary classification:
# Actual class 0: Replay Attack (Malicious)
# Actual class 1: Valid Telemetry (Benign)
# Predicted 0: Blocked
# Predicted 1: Allowed
cm_data = np.array([[500, 0], 
                    [0, 500]])

fig4, ax4 = plt.subplots(figsize=(6, 5))

# Plot the heatmap
# Using 'Blues' colormap for a professional IEEE look
sns.heatmap(cm_data, annot=True, fmt='d', cmap='Blues', cbar=True, ax=ax4, 
            annot_kws={"size": 14, "weight": "bold"}, square=True)

# Set labels for axes
ax4.set_xlabel('Predicted Class')
ax4.set_ylabel('Actual Class')
ax4.set_title('Intrusion Detection Efficacy: Replay Attacks', pad=20)

# Set tick labels
ax4.set_xticklabels(['Blocked (Malicious)', 'Allowed (Valid)'])
ax4.set_yticklabels(['Replay Attack', 'Valid Telemetry'], rotation=0)

fig4.tight_layout()
fig4.savefig('fig_confusion_matrix.png')


# ==========================================
# 3. FIGURE 5: LATENCY COMPARISON BAR CHART
# ==========================================
print("Generating Figure 5: Latency Comparison Bar Chart...")
fig5, ax5 = plt.subplots(figsize=(8, 5))

# Data Setup
systems = ['Baseline (Static UDP)', 'Proposed (Haptic-Seeded AES-GCM)']
network_latency = [1.20, 1.20]
crypto_overhead = [0.00, 0.44]

x = np.arange(len(systems))  # the label locations
width = 0.35  # the width of the bars

# Plotting the bars
# Baseline Network Latency
rects1_network = ax5.bar(x[0] - width/2, network_latency[0], width, 
                         label='Network Latency', color='lightgray', edgecolor='black', hatch='//')
# Baseline Crypto Overhead
rects1_crypto = ax5.bar(x[0] + width/2, crypto_overhead[0], width, 
                        label='Crypto Overhead', color='dimgray', edgecolor='black', hatch='\\\\')

# Proposed Network Latency
rects2_network = ax5.bar(x[1] - width/2, network_latency[1], width, 
                         color='lightgray', edgecolor='black', hatch='//')
# Proposed Crypto Overhead
rects2_crypto = ax5.bar(x[1] + width/2, crypto_overhead[1], width, 
                        color='dimgray', edgecolor='black', hatch='\\\\')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax5.set_ylabel('Processing Time (ms)')
ax5.set_title('End-to-End Processing Latency Comparison')
ax5.set_xticks(x)
ax5.set_xticklabels(systems)

# Make sure Y axis goes high enough to show the threshold line clearly
ax5.set_ylim(0, 2.5)

# Safety line
ax5.axhline(y=2.0, color='red', linestyle='--', linewidth=2, label='Maximum Safe Telesurgery Threshold')

ax5.legend(loc='upper left')
ax5.grid(True, axis='y', linestyle=':', alpha=0.6)

# Annotate values on top of bars
for rects in [rects1_network, rects1_crypto, rects2_network, rects2_crypto]:
    for rect in rects:
        height = rect.get_height()
        ax5.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

fig5.tight_layout()
fig5.savefig('fig_latency_bar_chart.png')

print("Success! Both IEEE-ready figures have been generated.")
