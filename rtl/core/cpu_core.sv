// Single-cycle RISC-V CPU Core
module cpu_core #(
    parameter DMEM_BASE_ADDR = 32'h00001000  // Data memory base address
) (
    input  logic        clk,          // Clock
    input  logic        rst_n,        // Active-low reset
    // Instruction memory interface
    output logic [31:0] imem_addr,    // Instruction memory address
    input  logic [31:0] imem_data,    // Instruction memory data
    // Data memory interface
    output logic [31:0] dmem_addr,    // Data memory address
    output logic [31:0] dmem_wdata,   // Data memory write data
    input  logic [31:0] dmem_rdata,   // Data memory read data
    output logic        dmem_we,      // Data memory write enable
    output logic [3:0]  dmem_be,      // Data memory byte enables
    output logic [1:0]  dmem_size,    // Data memory size
    // Debug interface
    output logic [31:0] debug_pc,     // Current PC value
    output logic [31:0] debug_instr   // Current instruction
);

    // Internal signals
    logic [31:0] pc_current;          // Current program counter
    logic [31:0] pc_next;             // Next program counter
    logic [31:0] pc_plus4;            // PC + 4
    logic [31:0] instruction;         // Current instruction
    
    // Instruction fields
    logic [6:0]  opcode;
    logic [4:0]  rd, rs1, rs2;
    logic [2:0]  funct3;
    
    // Control signals
    logic        reg_write;
    logic        alu_src;
    logic [3:0]  alu_op;
    logic        mem_write;
    logic [1:0]  mem_size;
    logic        branch;
    logic        jump;
    logic [1:0]  result_src;
    
    // Register file signals
    logic [31:0] rd_wdata;
    logic [31:0] rs1_data;
    logic [31:0] rs2_data;
    
    // ALU signals
    logic [31:0] alu_a;
    logic [31:0] alu_b;
    logic [31:0] alu_result;
    logic        alu_zero;
    logic        alu_negative;  // Used for branch comparisons
    
    // Immediate generation
    logic [31:0] imm_i_type;
    logic [31:0] imm_s_type;
    logic [31:0] imm_b_type;
    logic [31:0] imm_u_type;
    logic [31:0] imm_j_type;
    logic [31:0] imm_out;
    
    // Branch control
    logic        branch_taken;
    logic [31:0] branch_target;
    
    // Program Counter
    program_counter pc (
        .clk(clk),
        .rst_n(rst_n),
        .pc_next(pc_next),
        .pc_current(pc_current)
    );

    // Register file
    register_file regfile (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(rs1),
        .rs1_data(rs1_data),
        .rs2_addr(rs2),
        .rs2_data(rs2_data),
        .rd_addr(rd),
        .rd_data(rd_wdata),
        .we(reg_write)
    );

    // ALU
    wire unused_overflow;  // Unused output
    
    alu alu_inst (
        .a(alu_a),
        .b(alu_b),
        .op(alu_op),
        .result(alu_result),
        .zero(alu_zero),
        .negative(alu_negative),
        .overflow(unused_overflow)
    );

    // Control Unit
    wire [6:0] unused_funct7;  // Unused output
    wire       unused_mem_read; // Unused output
    
    control_unit ctrl (
        .instruction(instruction),
        .rd(rd),
        .rs1(rs1),
        .rs2(rs2),
        .opcode(opcode),
        .funct3(funct3),
        .funct7(unused_funct7),
        .reg_write(reg_write),
        .alu_src(alu_src),
        .alu_op(alu_op),
        .mem_write(mem_write),
        .mem_read(unused_mem_read),
        .mem_size(mem_size),
        .branch(branch),
        .jump(jump),
        .result_src(result_src)
    );

    // Immediate generation
    immediate_gen immgen (
        .instruction(instruction[31:7]),
        .i_type(imm_i_type),
        .s_type(imm_s_type),
        .b_type(imm_b_type),
        .u_type(imm_u_type),
        .j_type(imm_j_type)
    );

    // Instruction decoding is now handled by the control unit
    assign instruction = imem_data;

    // ALU operand selection
    assign alu_a = rs1_data;
    assign alu_b = alu_src ? imm_out : rs2_data;

    // Branch control
    always_comb begin
        case (funct3)
            3'b000:  branch_taken = branch && alu_zero;        // BEQ
            3'b001:  branch_taken = branch && !alu_zero;       // BNE
            3'b100:  branch_taken = branch && alu_negative;    // BLT
            3'b101:  branch_taken = branch && !alu_negative;   // BGE
            3'b110:  branch_taken = branch && alu_negative;    // BLTU
            3'b111:  branch_taken = branch && !alu_negative;   // BGEU
            default: branch_taken = 1'b0;
        endcase
    end
    
    assign branch_target = pc_current + imm_b_type;

    // Next PC calculation
    assign pc_plus4 = pc_current + 32'd4;
    always_comb begin
        if (jump) begin
            if (opcode == 7'b1100111) // JALR
                pc_next = {alu_result[31:1], 1'b0}; // Clear LSB
            else
                pc_next = pc_current + imm_j_type; // JAL
        end else if (branch_taken) begin
            pc_next = branch_target;
        end else begin
            pc_next = pc_plus4;
        end
    end

    // Memory interface
    logic [31:0] dmem_addr_offset;  // Address relative to data memory base
    logic        dmem_addr_valid;   // Whether the address is in valid range
    
    // Check if address is in valid range for data memory
    assign dmem_addr_valid = (alu_result >= DMEM_BASE_ADDR) && (alu_result < DMEM_BASE_ADDR + 32'h1000);
    assign dmem_addr_offset = dmem_addr_valid ? (alu_result - DMEM_BASE_ADDR) : 32'h0;
    
    // Byte enable logic
    always_comb begin
        dmem_be = 4'b0000;  // Default to no bytes enabled
        if (mem_write && dmem_addr_valid) begin
            case (mem_size)
                2'b00: begin  // Byte
                    case (alu_result[1:0])
                        2'b00: dmem_be = 4'b0001;
                        2'b01: dmem_be = 4'b0010;
                        2'b10: dmem_be = 4'b0100;
                        2'b11: dmem_be = 4'b1000;
                    endcase
                end
                2'b01: begin  // Half word
                    case (alu_result[1])
                        1'b0: dmem_be = 4'b0011;
                        1'b1: dmem_be = 4'b1100;
                    endcase
                end
                2'b10: begin  // Word
                    dmem_be = 4'b1111;
                end
                default: dmem_be = 4'b0000;
            endcase
        end
    end
    
    assign imem_addr = pc_current;
    assign dmem_addr = {dmem_addr_offset[31:2], 2'b00};  // Word-align the address
    assign dmem_wdata = rs2_data;  // No need to shift data, byte enables handle alignment
    assign dmem_we = mem_write && dmem_addr_valid;  // Only write if address is valid
    assign dmem_size = mem_size;

    // Immediate selection based on instruction type
    always_comb begin
        case (opcode)
            7'b0000011: imm_out = imm_i_type; // Load
            7'b0010011: imm_out = imm_i_type; // I-type
            7'b0100011: imm_out = imm_s_type; // Store
            7'b1100011: imm_out = imm_b_type; // Branch
            7'b0110111: imm_out = imm_u_type; // LUI
            7'b0010111: imm_out = imm_u_type; // AUIPC
            7'b1101111: imm_out = imm_j_type; // JAL
            7'b1100111: imm_out = imm_i_type; // JALR
            default:    imm_out = 32'b0;
        endcase
    end

    // Write-back data selection
    always_comb begin
        case (result_src)
            2'b00:   rd_wdata = alu_result;    // From ALU
            2'b01:   rd_wdata = dmem_rdata;    // From memory
            2'b10:   rd_wdata = pc_plus4;      // PC + 4 (for JAL/JALR)
            default: rd_wdata = alu_result;
        endcase
    end

    // Debug outputs
    assign debug_pc    = pc_current;
    assign debug_instr = instruction;

endmodule 
