
// Simple ands and inverters to understand AIG format

module aig_tests(in1,in2,my_out);
  
  input in1,in2;
  output my_out;
  
  assign my_out = in1 && in2;
  
endmodule :aig_tests
