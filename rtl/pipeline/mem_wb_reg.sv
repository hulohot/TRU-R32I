module mem_wb_reg (
    input  logic        clk,           // Clock
    input  logic        rst_n,         // Active-low reset
    
    // Control signals from MEM stage
    input  logic        mem_reg_write,   // Register write enable
    input  logic [1:0]  mem_result_src,  // Result source select
    
    // Data from MEM stage
    input  logic [31:0] mem_alu_result,  // ALU result
    input  logic [31:0] mem_read_data,   // Memory read data
    input  logic [4:0]  mem_rd_addr,     // Destination register
    input  logic [31:0] mem_pc_plus4,    // PC + 4 (for JAL/JALR)
    
    // Control signals to WB stage
    output logic        wb_reg_write,    // Register write enable
    output logic [1:0]  wb_result_src,   // Result source select
    
    // Data to WB stage
    output logic [31:0] wb_alu_result,   // ALU result
    output logic [31:0] wb_read_data,    // Memory read data
    output logic [4:0]  wb_rd_addr,      // Destination register
    output logic [31:0] wb_pc_plus4      // PC + 4 (for JAL/JALR)
);

    // Pipeline register updates
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset - clear all control signals
            wb_reg_write   <= 1'b0;
            wb_result_src <= 2'b0;
            
            // Clear data paths
            wb_alu_result <= 32'h0;
            wb_read_data  <= 32'h0;
            wb_rd_addr    <= 5'h0;
            wb_pc_plus4   <= 32'h0;
        end else begin
            // Normal operation - update all registers
            wb_reg_write   <= mem_reg_write;
            wb_result_src <= mem_result_src;
            
            wb_alu_result <= mem_alu_result;
            wb_read_data  <= mem_read_data;
            wb_rd_addr    <= mem_rd_addr;
            wb_pc_plus4   <= mem_pc_plus4;
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check register address is valid
        assert ({1'b0, mem_rd_addr} < 6'd32) else $error("Invalid rd_addr: %d", mem_rd_addr);
        
        // Check PC+4 alignment
        assert (mem_pc_plus4[1:0] == 2'b00) else $error("PC+4 not aligned to 4 bytes: %h", mem_pc_plus4);
    end
    // pragma translate_on

endmodule 
