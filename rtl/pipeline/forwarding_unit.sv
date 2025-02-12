module forwarding_unit (
    // Source register addresses from EX stage
    input  logic [4:0]  ex_rs1_addr,     // Source register 1 address
    input  logic [4:0]  ex_rs2_addr,     // Source register 2 address
    
    // Write-back control signals from MEM stage
    input  logic [4:0]  mem_rd_addr,     // Destination register address
    input  logic        mem_reg_write,    // Register write enable
    
    // Write-back control signals from WB stage
    input  logic [4:0]  wb_rd_addr,      // Destination register address
    input  logic        wb_reg_write,     // Register write enable
    
    // Forwarding control outputs
    output logic [1:0]  forward_a,        // Forwarding control for ALU input A
    output logic [1:0]  forward_b         // Forwarding control for ALU input B
);

    // Forward control values:
    // 2'b00: No forwarding (use register file output)
    // 2'b01: Forward from MEM stage
    // 2'b10: Forward from WB stage

    always_comb begin
        // Default: no forwarding
        forward_a = 2'b00;
        forward_b = 2'b00;

        // Check forwarding conditions for ALU input A (rs1)
        if (mem_reg_write && (mem_rd_addr != 5'b0) && (mem_rd_addr == ex_rs1_addr)) begin
            // Forward from MEM stage (higher priority)
            forward_a = 2'b01;
        end else if (wb_reg_write && (wb_rd_addr != 5'b0) && (wb_rd_addr == ex_rs1_addr)) begin
            // Forward from WB stage
            forward_a = 2'b10;
        end

        // Check forwarding conditions for ALU input B (rs2)
        if (mem_reg_write && (mem_rd_addr != 5'b0) && (mem_rd_addr == ex_rs2_addr)) begin
            // Forward from MEM stage (higher priority)
            forward_b = 2'b01;
        end else if (wb_reg_write && (wb_rd_addr != 5'b0) && (wb_rd_addr == ex_rs2_addr)) begin
            // Forward from WB stage
            forward_b = 2'b10;
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check that register addresses are valid
        assert ({1'b0, ex_rs1_addr} < 6'd32) else $error("Invalid rs1_addr: %d", ex_rs1_addr);
        assert ({1'b0, ex_rs2_addr} < 6'd32) else $error("Invalid rs2_addr: %d", ex_rs2_addr);
        assert ({1'b0, mem_rd_addr} < 6'd32) else $error("Invalid mem_rd_addr: %d", mem_rd_addr);
        assert ({1'b0, wb_rd_addr} < 6'd32) else $error("Invalid wb_rd_addr: %d", wb_rd_addr);

        // Verify forwarding logic
        if (forward_a != 2'b00) begin
            assert ((mem_reg_write && mem_rd_addr == ex_rs1_addr) ||
                   (wb_reg_write && wb_rd_addr == ex_rs1_addr))
            else $error("Invalid forwarding condition for input A");
        end

        if (forward_b != 2'b00) begin
            assert ((mem_reg_write && mem_rd_addr == ex_rs2_addr) ||
                   (wb_reg_write && wb_rd_addr == ex_rs2_addr))
            else $error("Invalid forwarding condition for input B");
        end
    end
    // pragma translate_on

endmodule 
