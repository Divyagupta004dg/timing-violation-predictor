module alu_8bit (
    input clk,
    input rst,
    input [2:0] op,
    input signed [7:0] a,
    input signed [7:0] b,
    output reg signed [7:0] result
);
    always @(posedge clk) begin
        if (rst) result <= 8'd0;
        else case(op)
            3'b000: result <= a + b;
            3'b001: result <= a - b;
            3'b010: result <= a & b;
            3'b011: result <= a | b;
            3'b100: result <= a ^ b;
            3'b101: result <= ~a;
            3'b110: result <= a << 1;
            3'b111: result <= a >> 1;
        endcase
    end
endmodule
