module multiplier_4bit (
    input clk,
    input rst,
    input [3:0] a,
    input [3:0] b,
    output reg [7:0] product
);
    always @(posedge clk) begin
        if (rst) product <= 8'd0;
        else product <= a * b;
    end
endmodule
