import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

# Load and train
df = pd.read_csv('dataset/timing_dataset.csv')
le = LabelEncoder()
df['design_enc'] = le.fit_transform(df['design'])

features = ['design_enc', 'clock_period_ns', 'input_delay', 'output_delay',
            'cell_count', 'chip_area', 'wns', 'tns']
X = df[features]
y = df['setup_violated']

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
xgb = XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
xgb.fit(X, y)

print("Models trained on full dataset.\n")

# Clock suggestion — use REAL wns from dataset
print("=== Minimum Safe Clock Per Design ===")
print(f"{'Design':>16} | {'Input Delay':>11} | {'Min Safe Clock':>14}")
print("-" * 48)

for design_name in ['mac_unit', 'alu_8bit', 'multiplier_4bit', 'counter_8bit']:
    d_enc = le.transform([design_name])[0]
    design_df = df[df['design'] == design_name]

    for delay in [0.2, 1.0, 2.0]:
        # Find minimum clock where violated=0 in actual data
        safe = design_df[
            (design_df['input_delay'] == delay) &
            (design_df['setup_violated'] == 0)
        ]['clock_period_ns'].min()

        if pd.isna(safe):
            print(f"{design_name:>16} | {delay:>11.1f} | {'Always fails':>14}")
        else:
            print(f"{design_name:>16} | {delay:>11.1f} | {safe:>14.1f} ns")

# Plot clock boundary per design
print("\n=== Generating clock boundary plot ===")
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
designs = ['mac_unit', 'alu_8bit', 'multiplier_4bit', 'counter_8bit']

for ax, design_name in zip(axes.flatten(), designs):
    d_df = df[(df['design'] == design_name) & (df['input_delay'] == 0.2)]
    colors = d_df['setup_violated'].map({0: 'green', 1: 'red'})
    ax.scatter(d_df['clock_period_ns'], d_df['wns'], c=colors, alpha=0.7)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.set_title(f'{design_name}')
    ax.set_xlabel('Clock Period (ns)')
    ax.set_ylabel('WNS (ns)')
    ax.legend(handles=[
        plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='green', label='Pass'),
        plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='red', label='Fail')
    ])

plt.suptitle('Timing Violation Boundary per Design', fontsize=14)
plt.tight_layout()
plt.savefig('ml/clock_boundary.png', dpi=150)
print("Saved: ml/clock_boundary.png")
print("\nDone!")
