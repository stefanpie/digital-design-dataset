module div(clk, ena, z, d, q, s);
  wire [16:0] _000_;
  wire [16:0] _001_;
  wire [16:0] _002_;
  wire [16:0] _003_;
  wire [16:0] _004_;
  wire [16:0] _005_;
  wire [16:0] _006_;
  wire [16:0] _007_;
  wire [16:0] _008_;
  wire [16:0] _009_;
  wire [16:0] _010_;
  wire [16:0] _011_;
  wire [16:0] _012_;
  wire [16:0] _013_;
  wire [16:0] _014_;
  wire [16:0] _015_;
  wire [16:0] _016_;
  wire [16:0] _017_;
  wire [16:0] _018_;
  wire [16:0] _019_;
  wire [16:0] _020_;
  wire [16:0] _021_;
  wire [16:0] _022_;
  wire [16:0] _023_;
  wire [16:0] _024_;
  wire [16:0] _025_;
  wire [16:0] _026_;
  wire [16:0] _027_;
  wire [16:0] _028_;
  wire [16:0] _029_;
  wire [16:0] _030_;
  wire [16:0] _031_;
  wire [16:0] _032_;
  wire [16:0] _033_;
  wire [16:0] _034_;
  wire [16:0] _035_;
  wire [16:0] _036_;
  wire [16:0] _037_;
  wire [16:0] _038_;
  wire [16:0] _039_;
  wire [16:0] _040_;
  wire [16:0] _041_;
  wire [16:0] _042_;
  wire [16:0] _043_;
  wire [16:0] _044_;
  wire [16:0] _045_;
  wire [16:0] _046_;
  wire [16:0] _047_;
  wire [16:0] _048_;
  wire [16:0] _049_;
  wire [16:0] _050_;
  wire [16:0] _051_;
  wire [16:0] _052_;
  wire [16:0] _053_;
  wire [16:0] _054_;
  wire [16:0] _055_;
  wire [16:0] _056_;
  wire [16:0] _057_;
  wire [16:0] _058_;
  wire [16:0] _059_;
  wire [16:0] _060_;
  wire [16:0] _061_;
  wire [16:0] _062_;
  wire [16:0] _063_;
  wire [16:0] _064_;
  wire [16:0] _065_;
  wire [16:0] _066_;
  wire [16:0] _067_;
  wire [16:0] _068_;
  wire [16:0] _069_;
  wire [16:0] _070_;
  wire [16:0] _071_;
  wire [16:0] _072_;
  wire [16:0] _073_;
  wire [16:0] _074_;
  wire [16:0] _075_;
  wire _076_;
  wire [16:0] _077_;
  wire [16:0] _078_;
  wire [16:0] _079_;
  wire [16:0] _080_;
  wire [16:0] _081_;
  wire [16:0] _082_;
  wire [16:0] _083_;
  wire [16:0] _084_;
  wire [16:0] _085_;
  wire [16:0] _086_;
  wire [16:0] _087_;
  wire [16:0] _088_;
  wire [16:0] _089_;
  wire [16:0] _090_;
  wire [16:0] _091_;
  wire [16:0] _092_;
  wire [16:0] _093_;
  wire [16:0] _094_;
  wire [16:0] _095_;
  wire [16:0] _096_;
  wire [16:0] _097_;
  wire [16:0] _098_;
  wire [16:0] _099_;
  wire [16:0] _100_;
  wire [16:0] _101_;
  wire [16:0] _102_;
  wire [16:0] _103_;
  wire [16:0] _104_;
  wire [16:0] _105_;
  wire [16:0] _106_;
  input clk;
  wire clk;
  input [7:0] d;
  wire [7:0] d;
  wire [16:0] \d_pipe[0] ;
  reg [16:0] \d_pipe[10] ;
  reg [16:0] \d_pipe[11] ;
  reg [16:0] \d_pipe[12] ;
  reg [16:0] \d_pipe[13] ;
  reg [16:0] \d_pipe[14] ;
  reg [16:0] \d_pipe[15] ;
  reg [16:0] \d_pipe[1] ;
  reg [16:0] \d_pipe[2] ;
  reg [16:0] \d_pipe[3] ;
  reg [16:0] \d_pipe[4] ;
  reg [16:0] \d_pipe[5] ;
  reg [16:0] \d_pipe[6] ;
  reg [16:0] \d_pipe[7] ;
  reg [16:0] \d_pipe[8] ;
  reg [16:0] \d_pipe[9] ;
  input ena;
  wire ena;
  wire [16:0] last_q;
  wire [31:0] n;
  output [15:0] q;
  wire [15:0] q;
  wire [16:0] \q_pipe[0] ;
  reg [16:0] \q_pipe[10] ;
  reg [16:0] \q_pipe[11] ;
  reg [16:0] \q_pipe[12] ;
  reg [16:0] \q_pipe[13] ;
  reg [16:0] \q_pipe[14] ;
  reg [16:0] \q_pipe[15] ;
  reg [16:0] \q_pipe[16] ;
  reg [16:0] \q_pipe[1] ;
  reg [16:0] \q_pipe[2] ;
  reg [16:0] \q_pipe[3] ;
  reg [16:0] \q_pipe[4] ;
  reg [16:0] \q_pipe[5] ;
  reg [16:0] \q_pipe[6] ;
  reg [16:0] \q_pipe[7] ;
  reg [16:0] \q_pipe[8] ;
  reg [16:0] \q_pipe[9] ;
  wire [16:0] qb_pipe;
  output [15:0] s;
  wire [15:0] s;
  wire [16:0] \s_pipe[0] ;
  reg [16:0] \s_pipe[10] ;
  reg [16:0] \s_pipe[11] ;
  reg [16:0] \s_pipe[12] ;
  reg [16:0] \s_pipe[13] ;
  reg [16:0] \s_pipe[14] ;
  reg [16:0] \s_pipe[15] ;
  wire [16:0] \s_pipe[16] ;
  reg [16:0] \s_pipe[1] ;
  reg [16:0] \s_pipe[2] ;
  reg [16:0] \s_pipe[3] ;
  reg [16:0] \s_pipe[4] ;
  reg [16:0] \s_pipe[5] ;
  reg [16:0] \s_pipe[6] ;
  reg [16:0] \s_pipe[7] ;
  reg [16:0] \s_pipe[8] ;
  reg [16:0] \s_pipe[9] ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$194.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$194.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$195.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$195.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$196.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$196.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$197.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$197.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$198.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$198.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$199.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$199.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$200.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$200.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$201.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$201.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$202.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$202.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$203.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$203.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$204.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$204.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$205.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$205.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$206.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$206.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$207.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$207.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$208.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$208.si ;
  wire [8:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$209.di ;
  wire [16:0] \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$209.si ;
  input [15:0] z;
  wire [15:0] z;
  assign _061_ = { z, 1'h0 } + { d[7], d, 8'h00 };
  assign _062_ = { \s_pipe[1] [15:0], 1'h0 } + \d_pipe[1] ;
  assign _063_ = { \s_pipe[2] [15:0], 1'h0 } + \d_pipe[2] ;
  assign _064_ = { \s_pipe[3] [15:0], 1'h0 } + \d_pipe[3] ;
  assign _065_ = { \s_pipe[4] [15:0], 1'h0 } + \d_pipe[4] ;
  assign _066_ = { \s_pipe[5] [15:0], 1'h0 } + \d_pipe[5] ;
  assign _067_ = { \s_pipe[6] [15:0], 1'h0 } + \d_pipe[6] ;
  assign _068_ = { \s_pipe[7] [15:0], 1'h0 } + \d_pipe[7] ;
  assign _069_ = { \s_pipe[8] [15:0], 1'h0 } + \d_pipe[8] ;
  assign _070_ = { \s_pipe[9] [15:0], 1'h0 } + \d_pipe[9] ;
  assign _071_ = { \s_pipe[10] [15:0], 1'h0 } + \d_pipe[10] ;
  assign _072_ = { \s_pipe[11] [15:0], 1'h0 } + \d_pipe[11] ;
  assign _073_ = { \s_pipe[12] [15:0], 1'h0 } + \d_pipe[12] ;
  assign _074_ = { \s_pipe[13] [15:0], 1'h0 } + \d_pipe[13] ;
  assign _075_ = { \s_pipe[14] [15:0], 1'h0 } + \d_pipe[14] ;
  assign _076_ = ! \q_pipe[15] [15];
  always @(posedge clk)
    \q_pipe[16]  <= _021_;
  always @(posedge clk)
    \q_pipe[1]  <= _022_;
  always @(posedge clk)
    \q_pipe[2]  <= _023_;
  always @(posedge clk)
    \q_pipe[3]  <= _024_;
  always @(posedge clk)
    \q_pipe[4]  <= _025_;
  always @(posedge clk)
    \q_pipe[5]  <= _026_;
  always @(posedge clk)
    \q_pipe[6]  <= _027_;
  always @(posedge clk)
    \q_pipe[7]  <= _028_;
  always @(posedge clk)
    \q_pipe[8]  <= _029_;
  always @(posedge clk)
    \q_pipe[9]  <= _030_;
  always @(posedge clk)
    \q_pipe[10]  <= _015_;
  always @(posedge clk)
    \q_pipe[11]  <= _016_;
  always @(posedge clk)
    \q_pipe[12]  <= _017_;
  always @(posedge clk)
    \q_pipe[13]  <= _018_;
  always @(posedge clk)
    \q_pipe[14]  <= _019_;
  always @(posedge clk)
    \q_pipe[15]  <= _020_;
  always @(posedge clk)
    \s_pipe[1]  <= _037_;
  always @(posedge clk)
    \s_pipe[2]  <= _038_;
  always @(posedge clk)
    \s_pipe[3]  <= _039_;
  always @(posedge clk)
    \s_pipe[4]  <= _040_;
  always @(posedge clk)
    \s_pipe[5]  <= _041_;
  always @(posedge clk)
    \s_pipe[6]  <= _042_;
  always @(posedge clk)
    \s_pipe[7]  <= _043_;
  always @(posedge clk)
    \s_pipe[8]  <= _044_;
  always @(posedge clk)
    \s_pipe[9]  <= _045_;
  always @(posedge clk)
    \s_pipe[10]  <= _031_;
  always @(posedge clk)
    \s_pipe[11]  <= _032_;
  always @(posedge clk)
    \s_pipe[12]  <= _033_;
  always @(posedge clk)
    \s_pipe[13]  <= _034_;
  always @(posedge clk)
    \s_pipe[14]  <= _035_;
  always @(posedge clk)
    \s_pipe[15]  <= _036_;
  always @(posedge clk)
    \d_pipe[1]  <= _006_;
  always @(posedge clk)
    \d_pipe[2]  <= _007_;
  always @(posedge clk)
    \d_pipe[3]  <= _008_;
  always @(posedge clk)
    \d_pipe[4]  <= _009_;
  always @(posedge clk)
    \d_pipe[5]  <= _010_;
  always @(posedge clk)
    \d_pipe[6]  <= _011_;
  always @(posedge clk)
    \d_pipe[7]  <= _012_;
  always @(posedge clk)
    \d_pipe[8]  <= _013_;
  always @(posedge clk)
    \d_pipe[9]  <= _014_;
  always @(posedge clk)
    \d_pipe[10]  <= _000_;
  always @(posedge clk)
    \d_pipe[11]  <= _001_;
  always @(posedge clk)
    \d_pipe[12]  <= _002_;
  always @(posedge clk)
    \d_pipe[13]  <= _003_;
  always @(posedge clk)
    \d_pipe[14]  <= _004_;
  always @(posedge clk)
    \d_pipe[15]  <= _005_;
  assign _021_ = ena ? { _076_, \q_pipe[15] [14:0], 1'h1 } : \q_pipe[16] ;
  assign _020_ = ena ? { \q_pipe[14] [15:0], qb_pipe[15] } : \q_pipe[15] ;
  assign _019_ = ena ? { \q_pipe[13] [15:0], qb_pipe[14] } : \q_pipe[14] ;
  assign _018_ = ena ? { \q_pipe[12] [15:0], qb_pipe[13] } : \q_pipe[13] ;
  assign _017_ = ena ? { \q_pipe[11] [15:0], qb_pipe[12] } : \q_pipe[12] ;
  assign _016_ = ena ? { \q_pipe[10] [15:0], qb_pipe[11] } : \q_pipe[11] ;
  assign _015_ = ena ? { \q_pipe[9] [15:0], qb_pipe[10] } : \q_pipe[10] ;
  assign _030_ = ena ? { \q_pipe[8] [15:0], qb_pipe[9] } : \q_pipe[9] ;
  assign _029_ = ena ? { \q_pipe[7] [15:0], qb_pipe[8] } : \q_pipe[8] ;
  assign _028_ = ena ? { \q_pipe[6] [15:0], qb_pipe[7] } : \q_pipe[7] ;
  assign _027_ = ena ? { \q_pipe[5] [15:0], qb_pipe[6] } : \q_pipe[6] ;
  assign _026_ = ena ? { \q_pipe[4] [15:0], qb_pipe[5] } : \q_pipe[5] ;
  assign _025_ = ena ? { \q_pipe[3] [15:0], qb_pipe[4] } : \q_pipe[4] ;
  assign _024_ = ena ? { \q_pipe[2] [15:0], qb_pipe[3] } : \q_pipe[3] ;
  assign _023_ = ena ? { \q_pipe[1] [15:0], qb_pipe[2] } : \q_pipe[2] ;
  assign _022_ = ena ? { 15'h0000, \q_pipe[0] [0], qb_pipe[1] } : \q_pipe[1] ;
  assign _077_ = qb_pipe[14] ? _106_ : _075_;
  assign _060_ = ena ? _077_ : 17'hxxxxx;
  assign _078_ = qb_pipe[13] ? _105_ : _074_;
  assign _059_ = ena ? _078_ : 17'hxxxxx;
  assign _079_ = qb_pipe[12] ? _104_ : _073_;
  assign _058_ = ena ? _079_ : 17'hxxxxx;
  assign _080_ = qb_pipe[11] ? _103_ : _072_;
  assign _057_ = ena ? _080_ : 17'hxxxxx;
  assign _081_ = qb_pipe[10] ? _102_ : _071_;
  assign _056_ = ena ? _081_ : 17'hxxxxx;
  assign _082_ = qb_pipe[9] ? _101_ : _070_;
  assign _055_ = ena ? _082_ : 17'hxxxxx;
  assign _083_ = qb_pipe[8] ? _100_ : _069_;
  assign _054_ = ena ? _083_ : 17'hxxxxx;
  assign _084_ = qb_pipe[7] ? _099_ : _068_;
  assign _053_ = ena ? _084_ : 17'hxxxxx;
  assign _085_ = qb_pipe[6] ? _098_ : _067_;
  assign _052_ = ena ? _085_ : 17'hxxxxx;
  assign _086_ = qb_pipe[5] ? _097_ : _066_;
  assign _051_ = ena ? _086_ : 17'hxxxxx;
  assign _087_ = qb_pipe[4] ? _096_ : _065_;
  assign _050_ = ena ? _087_ : 17'hxxxxx;
  assign _088_ = qb_pipe[3] ? _095_ : _064_;
  assign _049_ = ena ? _088_ : 17'hxxxxx;
  assign _089_ = qb_pipe[2] ? _094_ : _063_;
  assign _048_ = ena ? _089_ : 17'hxxxxx;
  assign _090_ = qb_pipe[1] ? _093_ : _062_;
  assign _047_ = ena ? _090_ : 17'hxxxxx;
  assign _091_ = \q_pipe[0] [0] ? _092_ : _061_;
  assign _046_ = ena ? _091_ : 17'hxxxxx;
  assign _036_ = ena ? _060_ : \s_pipe[15] ;
  assign _035_ = ena ? _059_ : \s_pipe[14] ;
  assign _034_ = ena ? _058_ : \s_pipe[13] ;
  assign _033_ = ena ? _057_ : \s_pipe[12] ;
  assign _032_ = ena ? _056_ : \s_pipe[11] ;
  assign _031_ = ena ? _055_ : \s_pipe[10] ;
  assign _045_ = ena ? _054_ : \s_pipe[9] ;
  assign _044_ = ena ? _053_ : \s_pipe[8] ;
  assign _043_ = ena ? _052_ : \s_pipe[7] ;
  assign _042_ = ena ? _051_ : \s_pipe[6] ;
  assign _041_ = ena ? _050_ : \s_pipe[5] ;
  assign _040_ = ena ? _049_ : \s_pipe[4] ;
  assign _039_ = ena ? _048_ : \s_pipe[3] ;
  assign _038_ = ena ? _047_ : \s_pipe[2] ;
  assign _037_ = ena ? _046_ : \s_pipe[1] ;
  assign _005_ = ena ? \d_pipe[14]  : \d_pipe[15] ;
  assign _004_ = ena ? \d_pipe[13]  : \d_pipe[14] ;
  assign _003_ = ena ? \d_pipe[12]  : \d_pipe[13] ;
  assign _002_ = ena ? \d_pipe[11]  : \d_pipe[12] ;
  assign _001_ = ena ? \d_pipe[10]  : \d_pipe[11] ;
  assign _000_ = ena ? \d_pipe[9]  : \d_pipe[10] ;
  assign _014_ = ena ? \d_pipe[8]  : \d_pipe[9] ;
  assign _013_ = ena ? \d_pipe[7]  : \d_pipe[8] ;
  assign _012_ = ena ? \d_pipe[6]  : \d_pipe[7] ;
  assign _011_ = ena ? \d_pipe[5]  : \d_pipe[6] ;
  assign _010_ = ena ? \d_pipe[4]  : \d_pipe[5] ;
  assign _009_ = ena ? \d_pipe[3]  : \d_pipe[4] ;
  assign _008_ = ena ? \d_pipe[2]  : \d_pipe[3] ;
  assign _007_ = ena ? \d_pipe[1]  : \d_pipe[2] ;
  assign _006_ = ena ? { d[7], d, 8'h00 } : \d_pipe[1] ;
  assign _092_ = { z, 1'h0 } - { d[7], d, 8'h00 };
  assign _093_ = { \s_pipe[1] [15:0], 1'h0 } - \d_pipe[1] ;
  assign _094_ = { \s_pipe[2] [15:0], 1'h0 } - \d_pipe[2] ;
  assign _095_ = { \s_pipe[3] [15:0], 1'h0 } - \d_pipe[3] ;
  assign _096_ = { \s_pipe[4] [15:0], 1'h0 } - \d_pipe[4] ;
  assign _097_ = { \s_pipe[5] [15:0], 1'h0 } - \d_pipe[5] ;
  assign _098_ = { \s_pipe[6] [15:0], 1'h0 } - \d_pipe[6] ;
  assign _099_ = { \s_pipe[7] [15:0], 1'h0 } - \d_pipe[7] ;
  assign _100_ = { \s_pipe[8] [15:0], 1'h0 } - \d_pipe[8] ;
  assign _101_ = { \s_pipe[9] [15:0], 1'h0 } - \d_pipe[9] ;
  assign _102_ = { \s_pipe[10] [15:0], 1'h0 } - \d_pipe[10] ;
  assign _103_ = { \s_pipe[11] [15:0], 1'h0 } - \d_pipe[11] ;
  assign _104_ = { \s_pipe[12] [15:0], 1'h0 } - \d_pipe[12] ;
  assign _105_ = { \s_pipe[13] [15:0], 1'h0 } - \d_pipe[13] ;
  assign _106_ = { \s_pipe[14] [15:0], 1'h0 } - \d_pipe[14] ;
  assign \q_pipe[0] [0] = z[15] ~^ d[0];
  assign qb_pipe[1] = \s_pipe[1] [16] ~^ \d_pipe[1] [8];
  assign qb_pipe[2] = \s_pipe[2] [16] ~^ \d_pipe[2] [8];
  assign qb_pipe[3] = \s_pipe[3] [16] ~^ \d_pipe[3] [8];
  assign qb_pipe[4] = \s_pipe[4] [16] ~^ \d_pipe[4] [8];
  assign qb_pipe[5] = \s_pipe[5] [16] ~^ \d_pipe[5] [8];
  assign qb_pipe[6] = \s_pipe[6] [16] ~^ \d_pipe[6] [8];
  assign qb_pipe[7] = \s_pipe[7] [16] ~^ \d_pipe[7] [8];
  assign qb_pipe[8] = \s_pipe[8] [16] ~^ \d_pipe[8] [8];
  assign qb_pipe[9] = \s_pipe[9] [16] ~^ \d_pipe[9] [8];
  assign qb_pipe[10] = \s_pipe[10] [16] ~^ \d_pipe[10] [8];
  assign qb_pipe[11] = \s_pipe[11] [16] ~^ \d_pipe[11] [8];
  assign qb_pipe[12] = \s_pipe[12] [16] ~^ \d_pipe[12] [8];
  assign qb_pipe[13] = \s_pipe[13] [16] ~^ \d_pipe[13] [8];
  assign qb_pipe[14] = \s_pipe[14] [16] ~^ \d_pipe[14] [8];
  assign qb_pipe[15] = \s_pipe[15] [16] ~^ \d_pipe[15] [8];
  assign \q_pipe[0] [16:1] = 16'h0000;
  assign \s_pipe[16] [15:0] = s;
  assign \s_pipe[0]  = { z[15], z };
  assign \d_pipe[0]  = { d[7], d, 8'h00 };
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$209.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$209.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$208.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$208.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$207.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$207.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$206.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$206.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$205.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$205.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$204.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$204.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$203.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$203.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$202.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$202.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$201.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$201.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$200.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$200.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$199.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$199.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$198.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$198.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$197.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$197.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$196.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$196.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$195.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$195.si  = 17'hxxxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$194.di  = 9'hxxx;
  assign \sc$func$/usr/scratch/skaram7/ddd_testing/db/designs/opencores__divider/sources/div.v:136$194.si  = 17'hxxxxx;
  assign last_q = \q_pipe[15] ;
  assign n = 32'd16;
  assign qb_pipe[0] = \q_pipe[0] [0];
  assign q = \q_pipe[16] [15:0];
endmodule