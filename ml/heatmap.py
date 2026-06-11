import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Train model
df = pd.read_csv('dataset/timing_dataset.csv')
le = LabelEncoder()
df['design_enc'] = le.fit_transform(df['design'])
features = ['design_enc','clock_period_ns','input_delay','output_delay',
            'cell_count','chip_area','wns','tns']
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(df[features], df['setup_violated'])

designs = ['mac_unit','alu_8bit','multiplier_4bit','counter_8bit']
clocks  = np.arange(3.0, 13.0, 0.5)
delays  = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

for ax, design_name in zip(axes.flatten(), designs):
    d_enc = le.transform([design_name])[0]
    design_df = df[df['design']==design_name]
    cell_count = design_df['cell_count'].iloc[0]
    chip_area  = design_df['chip_area'].iloc[0]

    # Build probability matrix
    matrix = []
    for delay in delays:
        row = []
        for clk in clocks:
            # Get real wns/tns from dataset if available
            match = design_df[
                (design_df['clock_period_ns']==clk) &
                (abs(design_df['input_delay']-delay)<0.01)
            ]
            if len(match) > 0:
                wns = match['wns'].iloc[0]
                tns = match['tns'].iloc[0]
            else:
                wns = 0.0
                tns = 0.0

            sample = pd.DataFrame([[d_enc, clk, delay, delay,
                                    cell_count, chip_area, wns, tns]],
                                  columns=features)
            prob = rf.predict_proba(sample)[0][1]
            row.append(prob * 100)
        matrix.append(row)

    matrix_df = pd.DataFrame(matrix,
                             index=[f"{d}ns" for d in delays],
                             columns=[f"{c}ns" for c in clocks])

    sns.heatmap(matrix_df, ax=ax, cmap='RdYlGn_r',
                vmin=0, vmax=100,
                annot=False, fmt='.0f',
                cbar_kws={'label': 'Violation Probability (%)'})

    ax.set_title(f'{design_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Clock Period (ns)')
    ax.set_ylabel('Input Delay (ns)')
    ax.tick_params(axis='x', rotation=45)

plt.suptitle('Setup Timing Violation Probability Heatmap\n(Red=High Risk, Green=Safe)',
             fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('ml/violation_heatmap.png', dpi=150, bbox_inches='tight')
print("Saved: ml/violation_heatmap.png")
