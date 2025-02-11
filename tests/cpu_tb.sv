`timescale 1ns/1ps

module cpu_tb;
    // Clock and reset
    logic clk;
    logic rst_n;
    
    // Debug signals
    logic [31:0] debug_pc;
    logic [31:0] debug_instruction;
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    // Test program memory
    logic [31:0] instr_mem [0:1023];  // 4KB instruction memory
    logic [31:0] data_mem [0:1023];   // 4KB data memory
    
    // Instruction memory interface
    logic [31:0] instr_addr;
    logic [31:0] instruction;
    
    // Data memory interface
    logic [31:0] data_addr;
    logic [31:0] data_wdata;
    logic [31:0] data_rdata;
    logic        data_we;
    logic [3:0]  data_be;
    
    // CPU instantiation
    cpu_core cpu (
        .clk              (clk),
        .rst_n            (rst_n),
        .instr_addr      (instr_addr),
        .instruction     (instruction),
        .data_addr       (data_addr),
        .data_wdata      (data_wdata),
        .data_rdata      (data_rdata),
        .data_we         (data_we),
        .data_be         (data_be),
        .debug_pc        (debug_pc),
        .debug_instruction(debug_instruction)
    );
    
    // Instruction memory read
    assign instruction = instr_mem[instr_addr[31:2]];
    
    // Data memory read/write
    always_ff @(posedge clk) begin
        if (data_we) begin
            // Write with byte enables
            if (data_be[0]) data_mem[data_addr[31:2]][7:0]   <= data_wdata[7:0];
            if (data_be[1]) data_mem[data_addr[31:2]][15:8]  <= data_wdata[15:8];
            if (data_be[2]) data_mem[data_addr[31:2]][23:16] <= data_wdata[23:16];
            if (data_be[3]) data_mem[data_addr[31:2]][31:24] <= data_wdata[31:24];
        end
        data_rdata <= data_mem[data_addr[31:2]];
    end
    
    // Test sequence
    initial begin
        // Initialize memories
        $readmemh("build/test_program.hex", instr_mem);
        for (int i = 0; i < 1024; i++) begin
            data_mem[i] = 32'h0;
        end
        
        // Reset sequence
        rst_n = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        
        // Run until test completion or timeout
        fork
            begin
                // Timeout after 1000 cycles
                repeat(1000) @(posedge clk);
                $display("TEST FAILED: Timeout");
                $finish;
            end
            begin
                // Wait for test completion
                while (1) begin
                    @(posedge clk);
                    // Check for test completion
                    if (cpu.reg_file.registers[31] == 32'h1) begin
                        $display("TEST PASSED");
                        $finish;
                    end
                    else if (cpu.reg_file.registers[31] == 32'hFFFFFFFF) begin
                        $display("TEST FAILED");
                        $finish;
                    end
                end
            end
        join_any
        disable fork;
    end
    
    // Debug output
    always @(posedge clk) begin
        $display("PC: %h, Instruction: %h", debug_pc, debug_instruction);
    end
    
endmodule 