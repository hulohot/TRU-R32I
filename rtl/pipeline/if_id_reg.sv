module if_id_reg (
    input  logic        clk,           // Clock
    input  logic        rst_n,         // Active-low reset
    input  logic        stall,         // Stall signal
    input  logic        flush,         // Flush signal (for branch/jump)
    
    // Inputs from IF stage
    input  logic [31:0] if_pc,         // Current PC
    input  logic [31:0] if_instruction,// Current instruction
    
    // Outputs to ID stage
    output logic [31:0] id_pc,         // PC for ID stage
    output logic [31:0] id_instruction // Instruction for ID stage
);

    // Pipeline register updates
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset to NOP instruction and PC=0
            id_pc          <= 32'h0;
            id_instruction <= 32'h00000013; // NOP (addi x0, x0, 0)
        end else if (flush) begin
            // Insert NOP on flush
            id_pc          <= if_pc;
            id_instruction <= 32'h00000013; // NOP
        end else if (!stall) begin
            // Normal operation - update registers
            id_pc          <= if_pc;
            id_instruction <= if_instruction;
        end
        // On stall, maintain current values
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check for valid instruction alignment
        assert ((if_pc[1:0] == 2'b00) && (id_pc[1:0] == 2'b00))
        else $error("PC not aligned to 4 bytes: if_pc=%h, id_pc=%h", if_pc, id_pc);
    end
    // pragma translate_on

endmodule 
