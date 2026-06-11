read_liberty /home/divya/OpenLane/designs/full_adder/runs/RUN_2026.01.16_13.45.09/issue_reproducible/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog reports/mac_netlist.v
link_design mac_unit
create_clock -name clk -period 10 [get_ports clk]
set_input_delay 0.5 -clock clk [all_inputs]
set_output_delay 0.5 -clock clk [all_outputs]
report_checks -path_delay max -fields {slew cap input nets fanout} -format full_clock_expanded
report_wns
report_tns
report_checks -path_delay min -fields {slew cap input nets fanout} -format full_clock_expanded
