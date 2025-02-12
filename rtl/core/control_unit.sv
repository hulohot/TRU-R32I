module control_unit (
    input  logic [31:0] instruction,    // Full 32-bit instruction
    
    // Decoded instruction fields
    output logic [4:0]  rd,           // Destination register
    output logic [4:0]  rs1,          // Source register 1
    output logic [4:0]  rs2,          // Source register 2
    output logic [6:0]  opcode,       // Operation code
    output logic [2:0]  funct3,       // Function code 3
    output logic [6:0]  funct7,       // Function code 7
    
    // Control signals
    output logic        reg_write,      // Register write enable
    output logic        alu_src,        // ALU source B select (0: rs2, 1: immediate)
    output logic [3:0]  alu_op,         // ALU operation type (4 bits)
    output logic        mem_write,      // Memory write enable
    output logic        mem_read,       // Memory read enable
    output logic [1:0]  mem_size,       // Memory access size (00: byte, 01: half, 10: word)
    output logic        branch,         // Branch instruction
    output logic        jump,           // Jump instruction
    output logic [1:0]  result_src      // Result source select (00: ALU, 01: Memory, 10: PC+4)
);

    // R-type instruction format:
    // funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    
    // Internal instruction field wires
    logic [6:0] opcode_int;
    logic [4:0] rd_int;
    logic [2:0] funct3_int;
    logic [4:0] rs1_int;
    logic [4:0] rs2_int;
    logic [6:0] funct7_int;
    
    // Instruction field decoding to internal wires
    assign opcode_int = instruction[6:0];
    assign rd_int     = instruction[11:7];
    assign funct3_int = instruction[14:12];
    assign rs1_int    = instruction[19:15];
    assign rs2_int    = instruction[24:20];
    assign funct7_int = instruction[31:25];
    
    // Output assignments
    assign opcode = opcode_int;
    assign rd     = rd_int;
    assign funct3 = funct3_int;
    assign rs1    = rs1_int;
    assign rs2    = rs2_int;
    assign funct7 = funct7_int;

    // ALU operation codes (matching ALU module)
    localparam ALU_ADD  = 4'b0000;  // Addition
    localparam ALU_SUB  = 4'b1000;  // Subtraction
    localparam ALU_SLL  = 4'b0001;  // Shift left logical
    localparam ALU_SLT  = 4'b0010;  // Set less than (signed)
    localparam ALU_SLTU = 4'b0011;  // Set less than unsigned
    localparam ALU_XOR  = 4'b0100;  // Bitwise XOR
    localparam ALU_SRL  = 4'b0101;  // Shift right logical
    localparam ALU_SRA  = 4'b1101;  // Shift right arithmetic
    localparam ALU_OR   = 4'b0110;  // Bitwise OR
    localparam ALU_AND  = 4'b0111;  // Bitwise AND
    localparam ALU_PASS = 4'b1001;  // Pass operand B (for LUI)

    // Main control logic
    always_comb begin
        // Default assignments
        reg_write = 1'b0;
        alu_src = 1'b0;
        alu_op = ALU_ADD;  // Default to ADD
        mem_write = 1'b0;
        mem_read = 1'b0;
        mem_size = 2'b10;  // Default to word size
        branch = 1'b0;
        jump = 1'b0;
        result_src = 2'b00;  // Default to ALU result

        case (opcode_int)
            7'b0110011: begin // R-type
                reg_write = 1'b1;
                alu_src = 1'b0;  // Use rs2
                case (funct3_int)
                    3'b000:  alu_op = (funct7_int[5]) ? ALU_SUB : ALU_ADD;
                    3'b001:  alu_op = ALU_SLL;
                    3'b010:  alu_op = ALU_SLT;
                    3'b011:  alu_op = ALU_SLTU;
                    3'b100:  alu_op = ALU_XOR;
                    3'b101:  alu_op = (funct7_int[5]) ? ALU_SRA : ALU_SRL;
                    3'b110:  alu_op = ALU_OR;
                    3'b111:  alu_op = ALU_AND;
                endcase
            end

            7'b0010011: begin // I-type ALU
                reg_write = 1'b1;
                alu_src = 1'b1;  // Use immediate
                case (funct3_int)
                    3'b000:  alu_op = ALU_ADD;  // ADDI
                    3'b001:  alu_op = ALU_SLL;  // SLLI
                    3'b010:  alu_op = ALU_SLT;  // SLTI
                    3'b011:  alu_op = ALU_SLTU; // SLTIU
                    3'b100:  alu_op = ALU_XOR;  // XORI
                    3'b101:  alu_op = (funct7_int[5]) ? ALU_SRA : ALU_SRL; // SRAI/SRLI
                    3'b110:  alu_op = ALU_OR;   // ORI
                    3'b111:  alu_op = ALU_AND;  // ANDI
                endcase
            end

            7'b0000011: begin // Load
                reg_write = 1'b1;
                alu_src = 1'b1;  // Use immediate
                alu_op = ALU_ADD; // Add for address
                mem_read = 1'b1;
                result_src = 2'b01; // From memory
                case (funct3_int)
                    3'b000:  mem_size = 2'b00; // LB
                    3'b001:  mem_size = 2'b01; // LH
                    3'b010:  mem_size = 2'b10; // LW
                    default: mem_size = 2'b10;
                endcase
            end

            7'b0100011: begin // Store
                alu_src = 1'b1;  // Use immediate
                alu_op = ALU_ADD; // Add for address
                mem_write = 1'b1;
                case (funct3_int)
                    3'b000:  mem_size = 2'b00; // SB
                    3'b001:  mem_size = 2'b01; // SH
                    3'b010:  mem_size = 2'b10; // SW
                    default: mem_size = 2'b10;
                endcase
            end

            7'b1100011: begin // Branch
                alu_src = 1'b0;  // Use rs2
                branch = 1'b1;
                case (funct3_int)
                    3'b000:  alu_op = ALU_SUB; // BEQ
                    3'b001:  alu_op = ALU_SUB; // BNE
                    3'b100:  alu_op = ALU_SLT; // BLT
                    3'b101:  alu_op = ALU_SLT; // BGE
                    3'b110:  alu_op = ALU_SLTU; // BLTU
                    3'b111:  alu_op = ALU_SLTU; // BGEU
                    default: alu_op = ALU_ADD;
                endcase
            end

            7'b1101111: begin // JAL
                reg_write = 1'b1;
                jump = 1'b1;
                result_src = 2'b10; // PC + 4
            end

            7'b1100111: begin // JALR
                reg_write = 1'b1;
                alu_src = 1'b1;  // Use immediate
                alu_op = ALU_ADD; // Add for address
                jump = 1'b1;
                result_src = 2'b10; // PC + 4
            end

            7'b0110111: begin // LUI
                reg_write = 1'b1;
                alu_src = 1'b1;  // Use immediate
                alu_op = ALU_PASS; // Pass immediate
            end

            7'b0010111: begin // AUIPC
                reg_write = 1'b1;
                alu_src = 1'b1;  // Use immediate
                alu_op = ALU_ADD; // Add PC + immediate
            end

            default: begin
                reg_write = 1'b0;
                alu_src = 1'b0;
                alu_op = ALU_ADD;
                mem_write = 1'b0;
                mem_read = 1'b0;
                mem_size = 2'b10;
                branch = 1'b0;
                jump = 1'b0;
                result_src = 2'b00;
            end
        endcase
    end

    // Assertions
    // pragma translate_off
    always_comb begin
        // Check for valid opcode
        assert ((opcode_int == 7'b0110011) || // R-type
                (opcode_int == 7'b0010011) || // I-type ALU
                (opcode_int == 7'b0000011) || // Load
                (opcode_int == 7'b0100011) || // Store
                (opcode_int == 7'b1100011) || // Branch
                (opcode_int == 7'b1101111) || // JAL
                (opcode_int == 7'b1100111) || // JALR
                (opcode_int == 7'b0110111) || // LUI
                (opcode_int == 7'b0010111))   // AUIPC
        else $warning("Invalid opcode: %b", opcode_int);

        // Check for valid funct3 based on opcode
        unique case (opcode_int)
            7'b0110011: // R-type
                assert ((funct3_int == 3'b000) || (funct3_int == 3'b001) || 
                        (funct3_int == 3'b010) || (funct3_int == 3'b011) ||
                        (funct3_int == 3'b100) || (funct3_int == 3'b101) ||
                        (funct3_int == 3'b110) || (funct3_int == 3'b111))
                else $error("Invalid funct3 for R-type: %b", funct3_int);
            
            7'b1100011: // Branch
                assert ((funct3_int == 3'b000) || (funct3_int == 3'b001) ||
                        (funct3_int == 3'b100) || (funct3_int == 3'b101) ||
                        (funct3_int == 3'b110) || (funct3_int == 3'b111))
                else $error("Invalid funct3 for branch: %b", funct3_int);
            
            7'b0000011: // Load
                assert ((funct3_int == 3'b000) || (funct3_int == 3'b001) ||
                        (funct3_int == 3'b010))
                else $error("Invalid funct3 for load: %b", funct3_int);
            
            7'b0100011: // Store
                assert ((funct3_int == 3'b000) || (funct3_int == 3'b001) ||
                        (funct3_int == 3'b010))
                else $error("Invalid funct3 for store: %b", funct3_int);
                
            default: begin end // Other opcodes don't care about funct3
        endcase
    end
    // pragma translate_on

endmodule
