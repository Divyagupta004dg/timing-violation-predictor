module shift_register (
    input clk,
    input rst,
    input din,
    output reg [7:0] q
);
    always @(posedge clk) begin
        if (rst) q <= 8'd0;
        else q <= {q[6:0], din};
    end
endmodule
