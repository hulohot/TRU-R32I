module instruction_memory #(
    parameter DEPTH = 1024,  // Memory depth in words
    parameter INIT_FILE = "" // Optional initialization file
) (
    input  logic [31:0] addr,         // Word-aligned address
    output logic [31:0] rdata         // Instruction output
);

    // Memory array
    logic [31:0] mem [DEPTH-1:0];
    
    // Address calculation
    logic [$clog2(DEPTH)-1:0] word_addr;
    
    always_comb begin
        // Default values
        word_addr = '0;
        rdata = 32'h00000013;  // Default to NOP instruction
        
        // Check for valid address (not X/Z and within range)
        if (!$isunknown(addr) && addr < (DEPTH << 2)) begin
            word_addr = ($clog2(DEPTH))'(addr >> 2);  // Cast to proper width
            rdata = mem[word_addr];
        end
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
        if (!$isunknown(addr)) begin
            // Address should be word-aligned
            assert ((addr & 32'h3) == 0) else
                $warning("Instruction fetch from non-word-aligned address: %h", addr);
                
            // Address should be within memory range
            assert (addr < (DEPTH << 2)) else
                $error("Instruction fetch from out-of-range address: %h", addr);
        end
    end
    // pragma translate_on

endmodule 
