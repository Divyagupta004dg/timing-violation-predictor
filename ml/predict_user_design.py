import subprocess
import sys
import os
import re
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

LIB = "/home/divya/OpenLane/designs/full_adder/runs/RUN_2026.01.16_13.45.09/issue_reproducible/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"

# ── Train model on existing dataset ──────────────────────
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
print("Models ready.\n")

# ── Get user inputs ───────────────────────────────────────
if len(sys.argv) < 4:
    print("Usage: python3 predict_user_design.py <file.v> <top_module> <clock_period_ns>")
    print("Example: python3 predict_user_design.py my_design.v my_alu 8.0")
    sys.exit(1)

verilog_file  = sys.argv[1]
top_module    = sys.argv[2]
clock_period  = float(sys.argv[3])
input_delay   = round(clock_period * 0.1, 2)  # 10% of clock period
output_delay  = input_delay

if not os.path.exists(verilog_file):
    print(f"ERROR: File not found: {verilog_file}")
    sys.exit(1)

print(f"Design file  : {verilog_file}")
print(f"Top module   : {top_module}")
print(f"Clock period : {clock_period} ns")
print(f"Input delay  : {input_delay} ns")
print("-" * 45)

# ── Step 1: Synthesis ─────────────────────────────────────
print("\n[1/4] Running Yosys synthesis...")
netlist_file = f"reports/user_{top_module}_netlist.v"
synth_log    = f"reports/user_{top_module}_synth.log"

synth_cmd = f"""
read_verilog {verilog_file}
hierarchy -check -top {top_module}
proc; opt; techmap; opt
dfflibmap -liberty {LIB}
abc -liberty {LIB}
stat -liberty {LIB}
write_verilog -noattr {netlist_file}
"""

result = subprocess.run(['yosys', '-p', synth_cmd],
                        capture_output=True, text=True)
with open(synth_log, 'w') as f:
    f.write(result.stdout + result.stderr)

# Extract cells and area
cells = 0
area  = 0.0
for line in result.stdout.splitlines():
    if 'Number of cells:' in line:
        cells = int(line.strip().split()[-1])
    if 'Chip area for module' in line:
        area = float(line.strip().split()[-1])

if cells == 0:
    print("ERROR: Synthesis failed. Check your Verilog file.")
    sys.exit(1)

print(f"    Cells : {cells}")
print(f"    Area  : {area:.2f} um2")

# ── Step 2: STA ───────────────────────────────────────────
print("\n[2/4] Running OpenSTA timing analysis...")
sta_script = f"""
read_liberty {LIB}
read_verilog {netlist_file}
link_design {top_module}
create_clock -name clk -period {clock_period} [get_ports clk]
set_input_delay {input_delay} -clock clk [all_inputs]
set_output_delay {output_delay} -clock clk [all_outputs]
report_wns
report_tns
report_checks -path_delay max -format short
exit
"""

sta_tcl = f"/tmp/user_sta_{top_module}.tcl"
with open(sta_tcl, 'w') as f:
    f.write(sta_script)

sta_result = subprocess.run(['sta', sta_tcl],
                            capture_output=True, text=True)
sta_out = sta_result.stdout

wns = 0.0
tns = 0.0
for line in sta_out.splitlines():
    if line.startswith('wns'):
        try: wns = float(line.split()[2])
        except: pass
    if line.startswith('tns'):
        try: tns = float(line.split()[2])
        except: pass

print(f"    WNS : {wns} ns")
print(f"    TNS : {tns} ns")

# ── Step 3: ML Prediction ─────────────────────────────────
print("\n[3/4] Running ML prediction...")

# Use median design encoding for unknown design
d_enc = df['design_enc'].median()

sample = pd.DataFrame([[d_enc, clock_period, input_delay, output_delay,
                        cells, area, wns, tns]], columns=features)

rf_pred  = rf.predict(sample)[0]
xgb_pred = xgb.predict(sample)[0]
rf_prob  = rf.predict_proba(sample)[0][1]
xgb_prob = xgb.predict_proba(sample)[0][1]

print(f"    Random Forest  : {'VIOLATED' if rf_pred else 'PASS'} (violation prob: {rf_prob*100:.1f}%)")
print(f"    XGBoost        : {'VIOLATED' if xgb_pred else 'PASS'} (violation prob: {xgb_prob*100:.1f}%)")

# ── Step 4: Suggest safe clock ────────────────────────────
print("\n[4/4] Finding minimum safe clock period...")

safe_clock = None
for clk in np.arange(0.5, 20.0, 0.5):
    # Run quick STA for this clock
    sta_q = f"""
read_liberty {LIB}
read_verilog {netlist_file}
link_design {top_module}
create_clock -name clk -period {clk} [get_ports clk]
set_input_delay {round(clk*0.1,2)} -clock clk [all_inputs]
set_output_delay {round(clk*0.1,2)} -clock clk [all_outputs]
report_wns
exit
"""
    with open('/tmp/sta_quick.tcl', 'w') as f:
        f.write(sta_q)
    r = subprocess.run(['sta', '/tmp/sta_quick.tcl'],
                       capture_output=True, text=True)
    w = 0.0
    for line in r.stdout.splitlines():
        if line.startswith('wns'):
            try: w = float(line.split()[2])
            except: pass
    if w >= 0.0:
        safe_clock = clk
        break

# ── Final Result ──────────────────────────────────────────
print("\n" + "="*45)
print("           PREDICTION RESULT")
print("="*45)
print(f"  Design        : {top_module}")
print(f"  Tested clock  : {clock_period} ns")
print(f"  WNS           : {wns} ns")
print(f"  TNS           : {tns} ns")
print(f"  Cells         : {cells}")
print(f"  Area          : {area:.2f} um2")
print("-"*45)

if rf_pred == 0 and xgb_pred == 0:
    print(f"  STATUS        : TIMING PASS ✓")
    print(f"  Clock {clock_period}ns is SAFE for this design.")
else:
    print(f"  STATUS        : TIMING VIOLATED ✗")
    if safe_clock:
        print(f"  SUGGESTION    : Use clock >= {safe_clock} ns")
        print(f"  (Minimum safe clock found by STA sweep)")
    else:
        print(f"  SUGGESTION    : Design too slow for tested range.")

print("="*45)
