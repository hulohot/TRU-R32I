module id_ex_reg (
    input  logic        clk,           // Clock
    input  logic        rst_n,         // Active-low reset
    input  logic        flush,         // Flush signal
    
    // Control signals from ID stage
    input  logic        id_reg_write,    // Register write enable
    input  logic        id_alu_src,      // ALU source select
    input  logic [3:0]  id_alu_op,       // ALU operation
    input  logic        id_mem_write,    // Memory write enable
    input  logic        id_mem_read,     // Memory read enable
    input  logic [1:0]  id_mem_size,     // Memory access size
    input  logic        id_branch,       // Branch instruction
    input  logic        id_jump,         // Jump instruction
    input  logic [1:0]  id_result_src,   // Result source select
    
    // Data from ID stage
    input  logic [31:0] id_pc,           // Program counter
    input  logic [31:0] id_rs1_data,     // Register source 1 data
    input  logic [31:0] id_rs2_data,     // Register source 2 data
    input  logic [31:0] id_imm,          // Immediate value
    input  logic [4:0]  id_rs1_addr,     // Register source 1 address
    input  logic [4:0]  id_rs2_addr,     // Register source 2 address
    input  logic [4:0]  id_rd_addr,      // Destination register address
    input  logic [2:0]  id_funct3,       // Function 3 field
    
    // Control signals to EX stage
    output logic        ex_reg_write,    // Register write enable
    output logic        ex_alu_src,      // ALU source select
    output logic [3:0]  ex_alu_op,       // ALU operation
    output logic        ex_mem_write,    // Memory write enable
    output logic        ex_mem_read,     // Memory read enable
    output logic [1:0]  ex_mem_size,     // Memory access size
    output logic        ex_branch,       // Branch instruction
    output logic        ex_jump,         // Jump instruction
    output logic [1:0]  ex_result_src,   // Result source select
    
    // Data to EX stage
    output logic [31:0] ex_pc,           // Program counter
    output logic [31:0] ex_rs1_data,     // Register source 1 data
    output logic [31:0] ex_rs2_data,     // Register source 2 data
    output logic [31:0] ex_imm,          // Immediate value
    output logic [4:0]  ex_rs1_addr,     // Register source 1 address
    output logic [4:0]  ex_rs2_addr,     // Register source 2 address
    output logic [4:0]  ex_rd_addr,      // Destination register address
    output logic [2:0]  ex_funct3        // Function 3 field
);

    // Pipeline register updates
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n || flush) begin
            // Reset or flush - clear all control signals
            ex_reg_write   <= 1'b0;
            ex_alu_src    <= 1'b0;
            ex_alu_op     <= 4'b0;
            ex_mem_write  <= 1'b0;
            ex_mem_read   <= 1'b0;
            ex_mem_size   <= 2'b0;
            ex_branch     <= 1'b0;
            ex_jump       <= 1'b0;
            ex_result_src <= 2'b0;
            
            // Clear data paths
            ex_pc         <= 32'h0;
            ex_rs1_data   <= 32'h0;
            ex_rs2_data   <= 32'h0;
            ex_imm        <= 32'h0;
            ex_rs1_addr   <= 5'h0;
            ex_rs2_addr   <= 5'h0;
            ex_rd_addr    <= 5'h0;
            ex_funct3     <= 3'h0;
        end else begin
            // Normal operation - update all registers
            ex_reg_write   <= id_reg_write;
            ex_alu_src    <= id_alu_src;
            ex_alu_op     <= id_alu_op;
            ex_mem_write  <= id_mem_write;
            ex_mem_read   <= id_mem_read;
            ex_mem_size   <= id_mem_size;
            ex_branch     <= id_branch;
            ex_jump       <= id_jump;
            ex_result_src <= id_result_src;
            
            ex_pc         <= id_pc;
            ex_rs1_data   <= id_rs1_data;
            ex_rs2_data   <= id_rs2_data;
            ex_imm        <= id_imm;
            ex_rs1_addr   <= id_rs1_addr;
            ex_rs2_addr   <= id_rs2_addr;
            ex_rd_addr    <= id_rd_addr;
            ex_funct3     <= id_funct3;
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check register addresses are valid
        assert ({1'b0, id_rs1_addr} < 6'd32) else $error("Invalid rs1_addr: %d", id_rs1_addr);
        assert ({1'b0, id_rs2_addr} < 6'd32) else $error("Invalid rs2_addr: %d", id_rs2_addr);
        assert ({1'b0, id_rd_addr} < 6'd32) else $error("Invalid rd_addr: %d", id_rd_addr);
        
        // Check PC alignment
        assert (id_pc[1:0] == 2'b00) else $error("PC not aligned to 4 bytes: %h", id_pc);
    end
    // pragma translate_on

endmodule 
