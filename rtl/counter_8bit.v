module counter_8bit (
    input clk,
    input rst,
    input en,
    input [7:0] load_val,
    input load,
    output reg [7:0] count
);
    always @(posedge clk) begin
        if (rst) count <= 8'd0;
        else if (load) count <= load_val;
        else if (en) count <= count + 1;
    end
endmodule
