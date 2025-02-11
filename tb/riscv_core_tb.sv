module riscv_core_tb;
    // Testbench signals
    logic        clk;
    logic        rst_n;
    logic [31:0] debug_pc;
    logic [31:0] debug_instr;

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // DUT instantiation
    riscv_core_top #(
        .IMEM_INIT_FILE("../build/test_program.hex"),
        .DMEM_INIT_FILE("")
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .debug_pc(debug_pc),
        .debug_instr(debug_instr)
    );

    // Test stimulus
    initial begin
        // Initialize
        rst_n = 0;
        
        // Wait a few cycles
        repeat(5) @(posedge clk);
        
        // Release reset
        rst_n = 1;
        
        // Run for 100 cycles or until we hit our test end condition
        repeat(100) begin
            @(posedge clk);
            
            // Print debug info
            $display("Time=%0t PC=%h Instr=%h", $time, debug_pc, debug_instr);
            
            // Check for test end condition (e.g. specific instruction or PC value)
            if (debug_instr == 32'h00000013) begin // NOP instruction
                $display("Test completed successfully!");
                $finish;
            end
        end
        
        // If we get here, test failed
        $display("Test failed - timeout after 100 cycles");
        $finish;
    end

    // Optional waveform dumping
    initial begin
        $dumpfile("riscv_core.vcd");
        $dumpvars(0, riscv_core_tb);
    end

endmodule 