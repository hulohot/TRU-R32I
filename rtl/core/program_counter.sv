// Program Counter for RISC-V CPU
module program_counter (
    input  logic        clk,            // Clock
    input  logic        rst_n,          // Active-low reset
    input  logic        stall,          // Stall signal
    input  logic        branch_taken,    // Branch taken signal
    input  logic [31:0] branch_target,  // Branch target address
    output logic [31:0] pc_current      // Current PC value
);

    // Next PC calculation
    logic [31:0] pc_next;
    
    always_comb begin
        if (stall) begin
            pc_next = pc_current;
        end else if (branch_taken) begin
            pc_next = branch_target;
        end else begin
            pc_next = pc_current + 32'd4;
        end
    end

    // Sequential logic for PC update
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_current <= 32'h0;  // Reset to address 0
        end else begin
            pc_current <= pc_next;
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check PC alignment (must be 4-byte aligned)
        assert ((pc_current[1:0] == 2'b00) && (pc_next[1:0] == 2'b00))
        else $error("PC not aligned to 4 bytes: current=%h, next=%h", pc_current, pc_next);
        
        // Check PC range (within valid memory range)
        assert (pc_current < 32'h1000_0000)  // Assuming 256MB address space
        else $error("PC out of valid range: %h", pc_current);

        // Check branch target alignment when branch is taken
        assert (!branch_taken || (branch_target[1:0] == 2'b00))
        else $error("Branch target not aligned to 4 bytes: %h", branch_target);
    end
    // pragma translate_on

endmodule 
