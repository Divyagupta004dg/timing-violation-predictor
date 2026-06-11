#!/bin/bash

LIB="/home/divya/OpenLane/designs/full_adder/runs/RUN_2026.01.16_13.45.09/issue_reproducible/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"

CSV="dataset/timing_dataset.csv"

# Append to existing CSV — header already exists
# If running fresh, uncomment next line:
# echo "design,clock_period_ns,input_delay,output_delay,cell_count,chip_area,wns,tns,setup_violated" > $CSV

COUNT=0

declare -A DESIGNS
DESIGNS["alu_8bit"]="alu_8bit"
DESIGNS["multiplier_4bit"]="multiplier_4bit"
DESIGNS["counter_8bit"]="counter_8bit"

for DESIGN in alu_8bit multiplier_4bit counter_8bit; do

    echo ""
    echo "=============================="
    echo "Design: $DESIGN"
    echo "=============================="

    for PERIOD in 3.0 3.5 4.0 4.5 5.0 5.5 6.0 6.5 7.0 7.5 8.0 8.5 9.0 9.5 10.0 10.5 11.0 11.5 12.0 12.5; do
      for IN_DELAY in 0.2 0.5 1.0 1.5 2.0; do

        OUT_DELAY=$IN_DELAY

        # Synthesis
        yosys -p "
            read_verilog rtl/${DESIGN}.v
            hierarchy -check -top ${DESIGN}
            proc; opt; techmap; opt
            dfflibmap -liberty $LIB
            abc -liberty $LIB
            stat -liberty $LIB
            write_verilog -noattr reports/${DESIGN}_netlist.v
        " > reports/synth_${DESIGN}_temp.log 2>&1

        CELLS=$(grep "Number of cells:" reports/synth_${DESIGN}_temp.log | awk '{print $NF}')
        AREA=$(grep "Chip area for module" reports/synth_${DESIGN}_temp.log | awk '{print $NF}')

        # STA
        cat > /tmp/sta_temp.tcl << STAEOF
read_liberty $LIB
read_verilog reports/${DESIGN}_netlist.v
link_design ${DESIGN}
create_clock -name clk -period ${PERIOD} [get_ports clk]
set_input_delay ${IN_DELAY} -clock clk [all_inputs]
set_output_delay ${OUT_DELAY} -clock clk [all_outputs]
report_wns
report_tns
exit
STAEOF

        STA_OUT=$(sta /tmp/sta_temp.tcl 2>/dev/null)
        WNS=$(echo "$STA_OUT" | grep "^wns" | awk '{print $3}')
        TNS=$(echo "$STA_OUT" | grep "^tns" | awk '{print $3}')
        WNS=${WNS:-0.0}
        TNS=${TNS:-0.0}

        if (( $(echo "$WNS < 0" | bc -l) )); then
            VIOLATED=1
        else
            VIOLATED=0
        fi

        echo "${DESIGN},${PERIOD},${IN_DELAY},${OUT_DELAY},${CELLS},${AREA},${WNS},${TNS},${VIOLATED}" >> $CSV
        COUNT=$((COUNT + 1))
        echo "  Row $COUNT | ${DESIGN} | clk=${PERIOD} | wns=$WNS | violated=$VIOLATED"

      done
    done
done

echo ""
echo "=== DONE: $COUNT new rows added ==="
wc -l $CSV
