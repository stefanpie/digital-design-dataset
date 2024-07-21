module submodule__counter (
    input wire clk,
    input wire rst,
    output wire [3:0] count
);
  reg [3:0] count_reg;

  always @(posedge clk or posedge rst) begin
    if (rst) begin
      count_reg <= 4'b0000;
    end else begin
      count_reg <= count_reg + 1;
    end
  end

  assign count = count_reg;
endmodule


module topmodule__squarewave (
    input wire clk,
    input wire rst,
    output wire [3:0] squarewave
);
  wire [3:0] count;

  submodule__counter counter (
      .clk  (clk),
      .rst  (rst),
      .count(count)
  );

  assign squarewave = count[3] ? 4'b1111 : 4'b0000;
endmodule

module topmodule__trianglewave (
    input wire clk,
    input wire rst,
    output wire [3:0] trianglewave
);
  wire [3:0] count;

  submodule__counter counter (
      .clk  (clk),
      .rst  (rst),
      .count(count)
  );

  assign trianglewave = count[3] ? ~count[3:0] : count[3:0];
endmodule
