/* verilator lint_off MULTITOP */
module cpu_core_pipelined #(
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

    // Pipeline control signals
    logic        stall_if;  // Stall fetch stage
    logic        stall_id;  // Stall decode stage
    logic        flush_if;  // Flush fetch stage
    logic        flush_id;  // Flush decode stage
    logic        flush_ex;  // Flush execute stage

    // Pipeline stage signals
    logic [31:0] if_pc;          // Current program counter
    logic [31:0] if_instruction; // Current instruction
    logic [31:0] if_pc_plus4;    // PC + 4
    logic        if_branch_taken;
    logic [31:0] if_branch_target;

    // ID stage signals
    logic [31:0] id_pc;
    logic [31:0] id_instruction;
    logic [4:0]  id_rs1_addr;
    logic [4:0]  id_rs2_addr;
    logic [4:0]  id_rd_addr;
    logic [2:0]  id_funct3;
    logic        id_reg_write;
    logic        id_alu_src;
    logic        id_mem_write;
    logic        id_mem_read;
    logic [1:0]  id_result_src;
    logic [31:0] id_rs1_data;
    logic [31:0] id_rs2_data;
    logic [31:0] id_imm;
    
    // Execute stage signals
    logic [31:0] ex_pc;
    logic [31:0] ex_rs1_data;
    logic [31:0] ex_rs2_data;
    logic [31:0] ex_imm;
    logic [4:0]  ex_rd_addr;
    logic [2:0]  ex_funct3;
    logic        ex_reg_write;
    logic        ex_alu_src;
    logic        ex_mem_write;
    logic        ex_mem_read;
    logic [1:0]  ex_result_src;
    logic [31:0] ex_alu_result;
    logic        ex_alu_zero;
    logic        ex_alu_negative;
    logic [31:0] ex_pc_plus4;
    
    // Memory stage signals
    logic [4:0]  mem_rd_addr;
    logic        mem_reg_write;
    logic        mem_mem_write;
    logic [1:0]  mem_mem_size;
    logic [1:0]  mem_result_src;
    logic [31:0] mem_alu_result;
    logic [31:0] mem_rs2_data;
    logic [31:0] mem_read_data;
    logic [31:0] mem_pc_plus4;
    
    // Writeback stage signals
    logic [4:0]  wb_rd_addr;
    logic        wb_reg_write;
    logic [1:0]  wb_result_src;
    logic [31:0] wb_alu_result;
    logic [31:0] wb_read_data;
    logic [31:0] wb_pc_plus4;
    logic [31:0] wb_write_data;
    
    // Control signals
    /* verilator lint_off UNUSEDSIGNAL */
    logic [3:0]  id_alu_op;
    logic [1:0]  id_mem_size;
    logic        id_branch;
    logic        id_jump;
    logic [3:0]  ex_alu_op;
    logic [1:0]  ex_mem_size;
    logic        ex_branch;
    logic        ex_jump;
    /* verilator lint_on UNUSEDSIGNAL */
    
    // Instruction fields
    /* verilator lint_off UNUSEDSIGNAL */
    logic [6:0] id_opcode;
    logic [6:0] id_funct7;
    /* verilator lint_on UNUSEDSIGNAL */
    
    // Forwarding unit
    logic [1:0] forward_a;
    logic [1:0] forward_b;
    
    forwarding_unit forwarding (
        // EX stage source registers
        .ex_rs1_addr(id_instruction[19:15]),
        .ex_rs2_addr(id_instruction[24:20]),
        
        // MEM stage signals
        .mem_rd_addr(mem_rd_addr),
        .mem_reg_write(mem_reg_write),
        
        // WB stage signals
        .wb_rd_addr(wb_rd_addr),
        .wb_reg_write(wb_reg_write),
        
        // Forwarding control outputs
        .forward_a(forward_a),
        .forward_b(forward_b)
    );

    // ALU input A forwarding mux
    logic [31:0] alu_input_a;
    always_comb begin
        case (forward_a)
            2'b00:   alu_input_a = ex_rs1_data;      // From register file
            2'b01:   alu_input_a = mem_alu_result;    // From MEM stage
            2'b10:   alu_input_a = wb_write_data;     // From WB stage
            default: alu_input_a = ex_rs1_data;
        endcase
    end

    // ALU input B forwarding mux
    logic [31:0] alu_input_b;
    always_comb begin
        if (ex_alu_src) begin
            alu_input_b = ex_imm;  // Use immediate
        end else begin
            case (forward_b)
                2'b00:   alu_input_b = ex_rs2_data;   // From register file
                2'b01:   alu_input_b = mem_rs2_data; // From MEM stage
                2'b10:   alu_input_b = wb_write_data;  // From WB stage
                default: alu_input_b = ex_rs2_data;
            endcase
        end
    end

    // Additional signal declarations
    /* verilator lint_off UNUSEDSIGNAL */
    logic        ex_overflow; // ALU overflow flag
    logic [31:0] s_type_imm; // S-type immediate
    logic [31:0] b_type_imm; // B-type immediate
    logic [31:0] u_type_imm; // U-type immediate
    logic [31:0] j_type_imm; // J-type immediate
    /* verilator lint_on UNUSEDSIGNAL */

    // Update ALU instance to use forwarded inputs
    alu alu_unit (
        .a(alu_input_a),
        .b(alu_input_b),
        .op(ex_alu_op),
        .result(ex_alu_result),
        .zero(ex_alu_zero),
        .negative(ex_alu_negative),
        .overflow(ex_overflow)
    );

    // Program Counter
    program_counter pc (
        .clk(clk),
        .rst_n(rst_n),
        .stall(stall_if),
        .branch_taken(if_branch_taken),
        .branch_target(if_branch_target),
        .pc_current(if_pc)
    );

    // IF stage
    assign if_pc_plus4 = if_pc + 32'd4;
    assign if_instruction = imem_data;
    assign imem_addr = if_pc;

    // IF/ID Pipeline Register
    if_id_reg if_id (
        .clk(clk),
        .rst_n(rst_n),
        .stall(stall_id),
        .flush(flush_if),
        .if_pc(if_pc),
        .if_instruction(if_instruction),
        .id_pc(id_pc),
        .id_instruction(id_instruction)
    );

    // ID stage
    // Register file
    register_file regfile (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(id_instruction[19:15]),
        .rs1_data(id_rs1_data),
        .rs2_addr(id_instruction[24:20]),
        .rs2_data(id_rs2_data),
        .rd_addr(wb_rd_addr),
        .rd_data(wb_write_data),
        .we(wb_reg_write)
    );

    // Control Unit
    control_unit ctrl (
        .instruction(id_instruction),
        .rd(id_rd_addr),
        .rs1(id_rs1_addr),
        .rs2(id_rs2_addr),
        .opcode(id_opcode),
        .funct3(id_funct3),
        .funct7(id_funct7),
        .reg_write(id_reg_write),
        .alu_src(id_alu_src),
        .alu_op(id_alu_op),
        .mem_write(id_mem_write),
        .mem_read(id_mem_read),
        .mem_size(id_mem_size),
        .branch(id_branch),
        .jump(id_jump),
        .result_src(id_result_src)
    );

    // Immediate generation
    logic [31:0] unused_s_type;
    logic [31:0] unused_b_type;
    logic [31:0] unused_u_type;
    logic [31:0] unused_j_type;

    immediate_gen immgen (
        .instruction(id_instruction[31:7]),
        .i_type(id_imm),
        .s_type(unused_s_type),  // Connect to internal signal
        .b_type(unused_b_type),  // Connect to internal signal
        .u_type(unused_u_type),  // Connect to internal signal
        .j_type(unused_j_type)   // Connect to internal signal
    );

    // Pipeline register unused signals
    logic [4:0] unused_ex_rs1_addr;
    logic [4:0] unused_ex_rs2_addr;
    logic unused_mem_mem_read;

    // ID/EX Pipeline Register
    id_ex_reg id_ex (
        .clk(clk),
        .rst_n(rst_n),
        .flush(flush_id),
        // Control signals from ID stage
        .id_reg_write(id_reg_write),
        .id_alu_src(id_alu_src),
        .id_alu_op(id_alu_op),
        .id_mem_write(id_mem_write),
        .id_mem_read(id_mem_read),
        .id_mem_size(id_mem_size),
        .id_branch(id_branch),
        .id_jump(id_jump),
        .id_result_src(id_result_src),
        // Data from ID stage
        .id_pc(id_pc),
        .id_rs1_data(id_rs1_data),
        .id_rs2_data(id_rs2_data),
        .id_imm(id_imm),
        .id_rs1_addr(id_rs1_addr),
        .id_rs2_addr(id_rs2_addr),
        .id_rd_addr(id_rd_addr),
        .id_funct3(id_funct3),
        // Control signals to EX stage
        .ex_reg_write(ex_reg_write),
        .ex_alu_src(ex_alu_src),
        .ex_alu_op(ex_alu_op),
        .ex_mem_write(ex_mem_write),
        .ex_mem_read(ex_mem_read),
        .ex_mem_size(ex_mem_size),
        .ex_branch(ex_branch),
        .ex_jump(ex_jump),
        .ex_result_src(ex_result_src),
        // Data to EX stage
        .ex_pc(ex_pc),
        .ex_rs1_data(ex_rs1_data),
        .ex_rs2_data(ex_rs2_data),
        .ex_imm(ex_imm),
        .ex_rs1_addr(unused_ex_rs1_addr),  // Connect to internal signal
        .ex_rs2_addr(unused_ex_rs2_addr),  // Connect to internal signal
        .ex_rd_addr(ex_rd_addr),
        .ex_funct3(ex_funct3)
    );

    // EX stage
    logic [31:0] ex_alu_input_a;
    logic [31:0] ex_alu_input_b;
    
    // ALU input selection (will be modified for forwarding)
    assign ex_alu_input_a = ex_rs1_data;
    assign ex_alu_input_b = ex_alu_src ? ex_imm : ex_rs2_data;
    
    // ALU
    alu alu_inst (
        .a(ex_alu_input_a),
        .b(ex_alu_input_b),
        .op(ex_alu_op),
        .result(ex_alu_result),
        .zero(ex_alu_zero),
        .negative(ex_alu_negative),
        .overflow(ex_overflow)
    );

    // Branch/Jump logic
    always_comb begin
        if (ex_jump) begin
            if (ex_funct3 == 3'b000)  // JALR
                if_branch_target = {ex_alu_result[31:1], 1'b0};
            else
                if_branch_target = ex_pc + ex_imm;  // JAL
            if_branch_taken = 1'b1;
        end else if (ex_branch) begin
            if_branch_target = ex_pc + ex_imm;
            case (ex_funct3)
                3'b000:  if_branch_taken = ex_alu_zero;         // BEQ
                3'b001:  if_branch_taken = !ex_alu_zero;        // BNE
                3'b100:  if_branch_taken = ex_alu_negative;     // BLT
                3'b101:  if_branch_taken = !ex_alu_negative;    // BGE
                3'b110:  if_branch_taken = ex_alu_negative;     // BLTU
                3'b111:  if_branch_taken = !ex_alu_negative;    // BGEU
                default: if_branch_taken = 1'b0;
            endcase
        end else begin
            if_branch_target = if_pc_plus4;
            if_branch_taken = 1'b0;
        end
    end

    assign ex_pc_plus4 = ex_pc + 32'd4;

    // EX/MEM Pipeline Register
    ex_mem_reg ex_mem (
        .clk(clk),
        .rst_n(rst_n),
        .flush(flush_ex),
        // Control signals from EX stage
        .ex_reg_write(ex_reg_write),
        .ex_mem_write(ex_mem_write),
        .ex_mem_read(ex_mem_read),
        .ex_mem_size(ex_mem_size),
        .ex_result_src(ex_result_src),
        // Data from EX stage
        .ex_alu_result(ex_alu_result),
        .ex_rs2_data(ex_rs2_data),
        .ex_rd_addr(ex_rd_addr),
        .ex_pc_plus4(ex_pc_plus4),
        // Control signals to MEM stage
        .mem_reg_write(mem_reg_write),
        .mem_mem_write(mem_mem_write),
        .mem_mem_read(unused_mem_mem_read),  // Connect to internal signal
        .mem_mem_size(mem_mem_size),
        .mem_result_src(mem_result_src),
        // Data to MEM stage
        .mem_alu_result(mem_alu_result),
        .mem_rs2_data(mem_rs2_data),
        .mem_rd_addr(mem_rd_addr),
        .mem_pc_plus4(mem_pc_plus4)
    );

    // MEM stage
    /* verilator lint_off UNUSEDSIGNAL */
    logic [31:0] mem_addr_offset;
    logic        mem_addr_valid;
    
    // Memory address validation
    assign mem_addr_valid = (mem_alu_result >= DMEM_BASE_ADDR) && 
                           (mem_alu_result < DMEM_BASE_ADDR + 32'h1000);
    assign mem_addr_offset = mem_addr_valid ? (mem_alu_result - DMEM_BASE_ADDR) : 32'h0;
    
    // Memory interface signals
    assign dmem_addr = {mem_addr_offset[31:2], 2'b00};
    assign dmem_wdata = mem_rs2_data;
    assign dmem_we = mem_mem_write && mem_addr_valid;
    assign dmem_size = mem_mem_size;
    
    // Byte enable logic
    always_comb begin
        dmem_be = 4'b0000;
        if (mem_mem_write && mem_addr_valid) begin
            case (mem_mem_size)
                2'b00: begin  // Byte
                    case (mem_alu_result[1:0])
                        2'b00: dmem_be = 4'b0001;
                        2'b01: dmem_be = 4'b0010;
                        2'b10: dmem_be = 4'b0100;
                        2'b11: dmem_be = 4'b1000;
                    endcase
                end
                2'b01: begin  // Half word
                    case (mem_alu_result[1])
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

    assign mem_read_data = dmem_rdata;

    // MEM/WB Pipeline Register
    mem_wb_reg mem_wb (
        .clk(clk),
        .rst_n(rst_n),
        // Control signals from MEM stage
        .mem_reg_write(mem_reg_write),
        .mem_result_src(mem_result_src),
        // Data from MEM stage
        .mem_alu_result(mem_alu_result),
        .mem_read_data(mem_read_data),
        .mem_rd_addr(mem_rd_addr),
        .mem_pc_plus4(mem_pc_plus4),
        // Control signals to WB stage
        .wb_reg_write(wb_reg_write),
        .wb_result_src(wb_result_src),
        // Data to WB stage
        .wb_alu_result(wb_alu_result),
        .wb_read_data(wb_read_data),
        .wb_rd_addr(wb_rd_addr),
        .wb_pc_plus4(wb_pc_plus4)
    );

    // WB stage
    always_comb begin
        case (wb_result_src)
            2'b00:   wb_write_data = wb_alu_result;    // From ALU
            2'b01:   wb_write_data = wb_read_data;     // From memory
            2'b10:   wb_write_data = wb_pc_plus4;      // PC + 4 (for JAL/JALR)
            default: wb_write_data = wb_alu_result;
        endcase
    end

    // Debug outputs
    assign debug_pc = if_pc;
    assign debug_instr = if_instruction;

    // Hazard detection unit
    hazard_detection hazard_unit (
        // ID stage signals
        .id_rs1_addr(id_instruction[19:15]),
        .id_rs2_addr(id_instruction[24:20]),
        
        // EX stage signals
        .ex_rd_addr(ex_rd_addr),
        .ex_mem_read(ex_mem_read),
        .ex_reg_write(ex_reg_write),
        
        // MEM stage signals
        .mem_rd_addr(mem_rd_addr),
        
        // Hazard control outputs
        .stall_if(stall_if),
        .stall_id(stall_id),
        .flush_if(flush_if),
        .flush_id(flush_id),
        .flush_ex(flush_ex)
    );

endmodule 
