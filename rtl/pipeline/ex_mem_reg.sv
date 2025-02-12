module ex_mem_reg (
    input  logic        clk,           // Clock
    input  logic        rst_n,         // Active-low reset
    input  logic        flush,         // Flush signal
    
    // Control signals from EX stage
    input  logic        ex_reg_write,    // Register write enable
    input  logic        ex_mem_write,    // Memory write enable
    input  logic        ex_mem_read,     // Memory read enable
    input  logic [1:0]  ex_mem_size,     // Memory access size
    input  logic [1:0]  ex_result_src,   // Result source select
    
    // Data from EX stage
    input  logic [31:0] ex_alu_result,   // ALU result
    input  logic [31:0] ex_rs2_data,     // Store data
    input  logic [4:0]  ex_rd_addr,      // Destination register
    input  logic [31:0] ex_pc_plus4,     // PC + 4 (for JAL/JALR)
    
    // Control signals to MEM stage
    output logic        mem_reg_write,   // Register write enable
    output logic        mem_mem_write,   // Memory write enable
    output logic        mem_mem_read,    // Memory read enable
    output logic [1:0]  mem_mem_size,    // Memory access size
    output logic [1:0]  mem_result_src,  // Result source select
    
    // Data to MEM stage
    output logic [31:0] mem_alu_result,  // ALU result
    output logic [31:0] mem_rs2_data,    // Store data
    output logic [4:0]  mem_rd_addr,     // Destination register
    output logic [31:0] mem_pc_plus4     // PC + 4 (for JAL/JALR)
);

    // Pipeline register updates
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n || flush) begin
            // Reset or flush - clear all control signals
            mem_reg_write   <= 1'b0;
            mem_mem_write  <= 1'b0;
            mem_mem_read   <= 1'b0;
            mem_mem_size   <= 2'b0;
            mem_result_src <= 2'b0;
            
            // Clear data paths
            mem_alu_result <= 32'h0;
            mem_rs2_data   <= 32'h0;
            mem_rd_addr    <= 5'h0;
            mem_pc_plus4   <= 32'h0;
        end else begin
            // Normal operation - update all registers
            mem_reg_write   <= ex_reg_write;
            mem_mem_write  <= ex_mem_write;
            mem_mem_read   <= ex_mem_read;
            mem_mem_size   <= ex_mem_size;
            mem_result_src <= ex_result_src;
            
            mem_alu_result <= ex_alu_result;
            mem_rs2_data   <= ex_rs2_data;
            mem_rd_addr    <= ex_rd_addr;
            mem_pc_plus4   <= ex_pc_plus4;
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check register address is valid
        assert ({1'b0, ex_rd_addr} < 6'd32) else $error("Invalid rd_addr: %d", ex_rd_addr);
        
        // Check memory size is valid
        assert (ex_mem_size <= 2'b10) else $error("Invalid memory size: %b", ex_mem_size);
        
        // Check PC+4 alignment
        assert (ex_pc_plus4[1:0] == 2'b00) else $error("PC+4 not aligned to 4 bytes: %h", ex_pc_plus4);
    end
    // pragma translate_on

endmodule 
