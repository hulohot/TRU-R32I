module hazard_detection (
    // Instruction fields from ID stage
    input  logic [4:0]  id_rs1_addr,     // Source register 1 address
    input  logic [4:0]  id_rs2_addr,     // Source register 2 address
    input  logic        id_branch,        // Branch instruction in ID
    input  logic        id_jump,          // Jump instruction in ID
    
    // Control signals from EX stage
    input  logic [4:0]  ex_rd_addr,      // Destination register address
    input  logic        ex_mem_read,      // Memory read signal
    input  logic        ex_reg_write,     // Register write enable
    input  logic        ex_branch_taken,  // Branch taken signal from EX stage
    
    // Control signals from MEM stage
    input  logic [4:0]  mem_rd_addr,     // Destination register address (for assertions)
    
    // Hazard control outputs
    output logic        stall_if,         // Stall fetch stage
    output logic        stall_id,         // Stall decode stage
    output logic        flush_if,         // Flush fetch stage
    output logic        flush_id,         // Flush decode stage
    output logic        flush_ex          // Flush execute stage
);

    // Internal signals
    logic load_use_hazard;
    logic branch_hazard;
    logic jump_hazard;
    logic control_hazard;
    logic rs1_ex_dependency;
    logic rs2_ex_dependency;

    // Register dependency checks for EX stage only
    assign rs1_ex_dependency = ex_reg_write && (ex_rd_addr == id_rs1_addr) && (id_rs1_addr != 5'b0);
    assign rs2_ex_dependency = ex_reg_write && (ex_rd_addr == id_rs2_addr) && (id_rs2_addr != 5'b0);

    // Load-use hazard detection - only check EX stage dependencies
    assign load_use_hazard = ex_mem_read && (rs1_ex_dependency || rs2_ex_dependency);

    // Control hazard detection
    assign branch_hazard = id_branch && ex_branch_taken;  // Only flush on taken branches
    assign jump_hazard = id_jump;  // Always flush on jumps
    assign control_hazard = branch_hazard || jump_hazard;

    // Hazard resolution
    always_comb begin
        // Default values
        stall_if = 1'b0;
        stall_id = 1'b0;
        flush_if = 1'b0;
        flush_id = 1'b0;
        flush_ex = 1'b0;

        // Priority: Load-use hazard takes precedence over control hazards
        if (load_use_hazard) begin
            // Load-use hazard: stall IF/ID and flush EX
            stall_if = 1'b1;
            stall_id = 1'b1;
            flush_ex = 1'b1;  // Flush EX to prevent incorrect execution
        end else if (control_hazard) begin
            // Control hazard (branch or jump): only flush pipeline
            flush_if = 1'b1;
            flush_id = 1'b1;
            flush_ex = 1'b1;
        end
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check that register addresses are valid
        assert (!$isunknown(id_rs1_addr)) else $error("Invalid rs1_addr: %d", id_rs1_addr);
        assert (!$isunknown(id_rs2_addr)) else $error("Invalid rs2_addr: %d", id_rs2_addr);
        assert (!$isunknown(ex_rd_addr)) else $error("Invalid ex_rd_addr: %d", ex_rd_addr);
        assert (!$isunknown(mem_rd_addr)) else $error("Invalid mem_rd_addr: %d", mem_rd_addr);

        // Verify hazard detection logic
        if (load_use_hazard) begin
            assert (ex_mem_read) else $error("Load-use hazard detected without load instruction");
            assert (rs1_ex_dependency || rs2_ex_dependency) 
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
