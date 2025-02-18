// Program Counter for RISC-V CPU
module program_counter #(
    parameter RESET_ADDR = 32'h00001000,  // Reset address (instruction memory base)
    parameter MAX_ADDR = 32'h00002000     // Maximum valid address
) (
    input  logic        clk,            // Clock
    input  logic        rst_n,          // Active-low reset
    input  logic        stall,          // Stall signal
    input  logic        branch_taken,    // Branch taken signal
    input  logic [31:2] branch_target,  // Word-aligned branch target address
    output logic [31:0] pc_current      // Current program counter
);

    // Next PC calculation
    logic [31:0] pc_next;
    
    // PC update logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_current <= RESET_ADDR;  // Reset to instruction memory base
        end else if (!stall) begin
            pc_current <= pc_next;
        end
    end
    
    // Next PC selection
    always_comb begin
        if (!rst_n) begin
            pc_next = RESET_ADDR;
        end else if (branch_taken) begin
            pc_next = {branch_target, 2'b00};  // Already word-aligned
        end else begin
            pc_next = pc_current + 32'd4;
        end
        
        // Assertions for PC alignment and range
        // pragma translate_off
        if (!$isunknown(pc_current) && rst_n) begin
            assert (pc_current[1:0] == 2'b00) else
                $error("PC not aligned to 4 bytes: current=%h", pc_current);
                
            assert (pc_current < MAX_ADDR) else
                $error("PC out of valid range: %h", pc_current);
                
            assert (pc_next[1:0] == 2'b00) else
                $error("Next PC not aligned to 4 bytes: %h", pc_next);
        end
        // pragma translate_on
    end

endmodule 
