module hazard_detection (
    // Instruction fields from ID stage
    input  logic [4:0]  id_rs1_addr,     // Source register 1 address
    input  logic [4:0]  id_rs2_addr,     // Source register 2 address
    
    // Control signals from EX stage
    input  logic [4:0]  ex_rd_addr,      // Destination register address
    input  logic        ex_mem_read,      // Memory read signal
    input  logic        ex_reg_write,     // Register write enable
    
    // Control signals from MEM stage
    input  logic [4:0]  mem_rd_addr,     // Destination register address
    
    // Hazard control outputs
    output logic        stall_if,         // Stall fetch stage
    output logic        stall_id,         // Stall decode stage
    output logic        flush_if,         // Flush fetch stage
    output logic        flush_id,         // Flush decode stage
    output logic        flush_ex          // Flush execute stage
);

    // Internal signals
    logic load_use_hazard;

    // Load-use hazard detection
    assign load_use_hazard = ex_mem_read && ex_reg_write && 
                            (ex_rd_addr != 5'b0) &&
                            ((ex_rd_addr == id_rs1_addr) || (ex_rd_addr == id_rs2_addr));

    // Stall and flush control
    assign stall_if = load_use_hazard;
    assign stall_id = load_use_hazard;
    assign flush_if = 1'b0;  // No need to flush IF stage
    assign flush_id = 1'b0;  // No need to flush ID stage
    assign flush_ex = load_use_hazard;

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check that register addresses are valid
        assert ({1'b0, id_rs1_addr} < 6'd32) else $error("Invalid rs1_addr: %d", id_rs1_addr);
        assert ({1'b0, id_rs2_addr} < 6'd32) else $error("Invalid rs2_addr: %d", id_rs2_addr);
        assert ({1'b0, ex_rd_addr} < 6'd32) else $error("Invalid ex_rd_addr: %d", ex_rd_addr);
        assert ({1'b0, mem_rd_addr} < 6'd32) else $error("Invalid mem_rd_addr: %d", mem_rd_addr);

        // Verify hazard detection logic
        if (load_use_hazard) begin
            assert (ex_mem_read && ex_reg_write) 
            else $error("Load-use hazard detected without load instruction");
            
            assert (ex_rd_addr != 5'b0 && 
                   (ex_rd_addr == id_rs1_addr || ex_rd_addr == id_rs2_addr))
            else $error("Load-use hazard detected without register dependency");
        end

        // Verify that stalls and flushes are not active simultaneously for the same stage
        assert (!(stall_if && flush_if)) 
        else $error("IF stage cannot be stalled and flushed simultaneously");
        
        assert (!(stall_id && flush_id))
        else $error("ID stage cannot be stalled and flushed simultaneously");
    end
    // pragma translate_on

endmodule 
