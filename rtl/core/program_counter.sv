// Program Counter for RISC-V CPU
module program_counter (
    input  logic        clk,          // Clock
    input  logic        rst_n,        // Active-low reset
    input  logic [31:0] pc_next,      // Next PC value
    output logic [31:0] pc_current    // Current PC value
);

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
    end
    // pragma translate_on

endmodule 
