module riscv_core_top #(
    parameter IMEM_DEPTH = 1024,  // Instruction memory depth in words
    parameter DMEM_DEPTH = 1024,  // Data memory depth in words
    parameter IMEM_INIT_FILE = "", // Optional instruction memory initialization file
    parameter DMEM_INIT_FILE = ""  // Optional data memory initialization file
) (
    input  logic        clk,          // Clock
    input  logic        rst_n,        // Active-low reset
    // Debug interface
    output logic [31:0] debug_pc,     // Current PC value
    output logic [31:0] debug_instr   // Current instruction
);

    // Internal signals
    logic [31:0] imem_addr;
    logic [31:0] imem_data;
    logic [31:0] dmem_addr;
    logic [31:0] dmem_wdata;
    logic [31:0] dmem_rdata;
    logic        dmem_we;
    /* verilator lint_off UNUSEDSIGNAL */
    logic [1:0]  dmem_size;
    /* verilator lint_on UNUSEDSIGNAL */
    logic [3:0]  dmem_be;

    // CPU Core
    cpu_core #(
        .DMEM_BASE_ADDR(32'h00001000)  // Data memory base address from linker script
    ) cpu (
        .clk(clk),
        .rst_n(rst_n),
        // Instruction memory interface
        .imem_addr(imem_addr),
        .imem_data(imem_data),
        // Data memory interface
        .dmem_addr(dmem_addr),
        .dmem_wdata(dmem_wdata),
        .dmem_rdata(dmem_rdata),
        .dmem_we(dmem_we),
        .dmem_be(dmem_be),
        .dmem_size(dmem_size),
        // Debug interface
        .debug_pc(debug_pc),
        .debug_instr(debug_instr)
    );

    // Instruction Memory
    instruction_memory #(
        .DEPTH(IMEM_DEPTH),
        .INIT_FILE(IMEM_INIT_FILE)
    ) imem (
        .clk(clk),
        .addr(imem_addr),
        .rdata(imem_data)
    );

    // Data Memory
    data_memory #(
        .DEPTH(DMEM_DEPTH),
        .INIT_FILE(DMEM_INIT_FILE),
        .BASE_ADDR(32'h00001000)  // Data memory base address from linker script
    ) dmem (
        .clk(clk),
        .rst_n(rst_n),
        .addr(dmem_addr),
        .wdata(dmem_wdata),
        .we(dmem_we),
        .be(dmem_be),
        .rdata(dmem_rdata)
    );

endmodule 
