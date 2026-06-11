module mac_unit (
    input clk,
    input rst,
    input signed [7:0] a,
    input signed [7:0] b,
    output reg signed [15:0] acc
);

    reg signed [15:0] mult_reg;

    // Stage 1: Multiply
    always @(posedge clk) begin
        if (rst)
            mult_reg <= 16'd0;
        else
            mult_reg <= a * b;
    end

    // Stage 2: Accumulate
    always @(posedge clk) begin
        if (rst)
            acc <= 16'd0;
        else
            acc <= acc + mult_reg;
    end

endmodule
