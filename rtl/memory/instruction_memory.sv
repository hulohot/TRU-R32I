module instruction_memory #(
    parameter DEPTH = 1024,  // Memory depth in words
    parameter INIT_FILE = "" // Optional initialization file
) (
    input  logic        clk,          // Clock
    input  logic [31:0] addr,         // Word-aligned address
    output logic [31:0] rdata         // Instruction output
);

    // Memory array
    logic [31:0] mem [DEPTH-1:0];
    
    // Address selection (only use bits needed to index memory)
    logic [$clog2(DEPTH)-1:0] word_addr;
    assign word_addr = addr[($clog2(DEPTH)+1):2];
    
    // Read-only memory - synchronous read
    always_ff @(posedge clk) begin
        // Address is word-aligned (ignore bottom 2 bits)
        rdata <= mem[word_addr];
    end

    // Memory initialization
    initial begin
        if (INIT_FILE != "") begin
            $readmemh(INIT_FILE, mem);
        end else begin
            // Initialize with NOP instructions (RISC-V: addi x0, x0, 0)
            for (int i = 0; i < DEPTH; i++) begin
                mem[i] = 32'h00000013;
            end
        end
    end

    // Assertions
    // pragma translate_off
    initial begin
        // Verify memory size is reasonable
        assert (DEPTH <= 262144) else  // Max 1MB (262144 words)
            $error("Memory size exceeds maximum allowed (1MB)");
    end
    
    always_comb begin
        // Address should be word-aligned
        assert ((addr & 32'h3) == 0) else
            $warning("Instruction fetch from non-word-aligned address: %h", addr);
            
        // Address should be within memory range
        assert (int'(word_addr) < int'(DEPTH)) else
            $error("Instruction fetch from out-of-range address: %h", addr);
    end
    // pragma translate_on

endmodule 
