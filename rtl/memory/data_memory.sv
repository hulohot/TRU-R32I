// Data Memory Module for RISC-V CPU
// Supports byte, half-word, and word accesses
module data_memory #(
    parameter DEPTH = 1024,  // Memory depth in words
    parameter INIT_FILE = "", // Optional initialization file
    parameter BASE_ADDR = 32'h00001000  // Base address for data memory
) (
    input  logic        clk,          // Clock
    input  logic        rst_n,        // Active-low reset
    input  logic [31:0] addr,         // Byte address
    input  logic [31:0] wdata,        // Write data
    input  logic        we,           // Write enable
    input  logic [3:0]  be,           // Byte enable
    output logic [31:0] rdata         // Read data
);

    // Memory array (byte addressable)
    logic [7:0] mem [DEPTH*4-1:0];
    
    // Internal signals
    logic [31:0] base_addr;
    /* verilator lint_off UNUSEDSIGNAL */
    logic [31:0] local_addr;
    /* verilator lint_on UNUSEDSIGNAL */
    
    // Calculate local address by subtracting base address
    assign local_addr = addr - BASE_ADDR;
    // Calculate word-aligned base address
    assign base_addr = {local_addr[31:2], 2'b00};
    
    // Read operation (asynchronous)
    always_comb begin
        // Default to zero
        rdata = 32'h0;
        
        // Only read if address is in valid range
        if (addr >= BASE_ADDR && addr < BASE_ADDR + DEPTH*4) begin
            // Read individual bytes based on address
            rdata[7:0]   = mem[base_addr];
            rdata[15:8]  = mem[base_addr + 1];
            rdata[23:16] = mem[base_addr + 2];
            rdata[31:24] = mem[base_addr + 3];
        end
    end

    // Write operation (synchronous)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset memory if initialization file not provided
            if (INIT_FILE == "") begin
                for (int i = 0; i < DEPTH*4; i++) begin
                    mem[i] <= 8'h0;
                end
            end
        end else if (we && addr >= BASE_ADDR && addr < BASE_ADDR + DEPTH*4) begin
            // Write individual bytes based on byte enable
            if (be[0]) mem[base_addr]     <= wdata[7:0];
            if (be[1]) mem[base_addr + 1] <= wdata[15:8];
            if (be[2]) mem[base_addr + 2] <= wdata[23:16];
            if (be[3]) mem[base_addr + 3] <= wdata[31:24];
        end
    end

    // Initialization from file if provided
    initial begin
        if (INIT_FILE != "") begin
            $readmemh(INIT_FILE, mem);
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check address alignment based on byte enables
        if (we && addr >= BASE_ADDR && addr < BASE_ADDR + DEPTH*4) begin
            // Word access must be word-aligned
            if (be == 4'b1111)
                assert (addr[1:0] == 2'b00)
                else $error("Word access not word-aligned: addr = %h", addr);
            
            // Half-word access must be half-word-aligned
            if (be == 4'b0011 || be == 4'b1100)
                assert (addr[0] == 1'b0)
                else $error("Half-word access not half-word-aligned: addr = %h", addr);
            
            // Byte enables must be contiguous
            assert (be == 4'b0001 || be == 4'b0010 || be == 4'b0100 || be == 4'b1000 ||  // Single byte
                   be == 4'b0011 || be == 4'b1100 ||                                      // Half word
                   be == 4'b1111)                                                         // Full word
                else $error("Invalid byte enable pattern: be = %b", be);
        end

        // Check address range
        assert (addr >= BASE_ADDR && addr < BASE_ADDR + DEPTH*4 || !we)
            else $error("Address out of range: addr = %h", addr);
    end
    // pragma translate_on

endmodule 
