// Register File for RISC-V CPU
// 32 x 32-bit registers with x0 hardwired to 0
module register_file (
    input  logic        clk,       // Clock
    input  logic        rst_n,     // Active-low reset
    
    // Read port 1
    input  logic [4:0]  rs1_addr,    // Source register 1 address
    output logic [31:0] rs1_data,    // Source register 1 data
    
    // Read port 2
    input  logic [4:0]  rs2_addr,    // Source register 2 address
    output logic [31:0] rs2_data,    // Source register 2 data
    
    // Write port
    input  logic [4:0]  rd_addr,     // Destination register address
    input  logic [31:0] rd_data,     // Write data
    input  logic        we           // Write enable
);

    // Register array (x0-x31)
    logic [31:0] registers [0:31];

    // Asynchronous read
    // Read before write - return old value during concurrent read/write
    assign rs1_data = (rs1_addr == 5'b0) ? 32'b0 : registers[rs1_addr];
    assign rs2_data = (rs2_addr == 5'b0) ? 32'b0 : registers[rs2_addr];

    // Synchronous write with asynchronous reset
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all registers to 0
            for (int i = 0; i < 32; i++) begin
                registers[i] <= 32'b0;
            end
        end else if (we && rd_addr != 5'b0) begin
            // Write to register if enabled and not x0
            registers[rd_addr] <= rd_data;
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check that register addresses are valid (0-31)
        // Using 6-bit comparisons to avoid width truncation
        assert ({1'b0, rs1_addr} < 6'd32) else $error("Invalid rs1_addr: %d", rs1_addr);
        assert ({1'b0, rs2_addr} < 6'd32) else $error("Invalid rs2_addr: %d", rs2_addr);
        assert ({1'b0, rd_addr} < 6'd32) else $error("Invalid rd_addr: %d", rd_addr);
    end
    // pragma translate_on

endmodule 
