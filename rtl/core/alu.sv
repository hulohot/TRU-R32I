// ALU for RISC-V RV32I CPU
// Implements all arithmetic and logical operations from the RV32I ISA

module alu (
    input  logic [31:0] a,            // First operand
    input  logic [31:0] b,            // Second operand
    input  logic [3:0]  op,           // Operation to perform
    output logic [31:0] result,       // Result of operation
    output logic        zero,         // Result is zero
    output logic        negative,     // Result is negative
    output logic        overflow      // Result overflowed
);

    // Operation codes
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
    localparam ALU_PASS = 4'b1001;  // Pass operand B

    // Internal signals
    logic [31:0] add_sub_result;
    logic        add_sub_overflow;
    logic [31:0] shift_result;
    logic [31:0] logic_result;
    logic [31:0] compare_result;

    // Addition/subtraction
    always_comb begin
        case (op)
            ALU_SUB: begin
                {add_sub_overflow, add_sub_result} = {1'b0, a} - {1'b0, b};
                // Overflow occurs when:
                // 1. Subtracting a negative from a positive yields a negative (pos - neg = neg)
                // 2. Subtracting a positive from a negative yields a positive (neg - pos = pos)
                add_sub_overflow = (a[31] != b[31]) && (add_sub_result[31] == b[31]);
            end
            default: begin // ADD
                {add_sub_overflow, add_sub_result} = {1'b0, a} + {1'b0, b};
                // Overflow occurs when:
                // 1. Adding two positives yields a negative (pos + pos = neg)
                // 2. Adding two negatives yields a positive (neg + neg = pos)
                add_sub_overflow = (a[31] == b[31]) && (add_sub_result[31] != a[31]);
            end
        endcase
    end

    // Shift operations
    always_comb begin
        case (op)
            ALU_SLL: shift_result = a << b[4:0];
            ALU_SRL: shift_result = a >> b[4:0];
            ALU_SRA: shift_result = $signed(a) >>> b[4:0];
            default: shift_result = a;
        endcase
    end

    // Logic operations
    always_comb begin
        case (op)
            ALU_XOR:  logic_result = a ^ b;
            ALU_OR:   logic_result = a | b;
            ALU_AND:  logic_result = a & b;
            ALU_PASS: logic_result = b;
            default:  logic_result = a;
        endcase
    end

    // Comparison operations
    always_comb begin
        case (op)
            ALU_SLT:  compare_result = {31'b0, $signed(a) < $signed(b)};
            ALU_SLTU: compare_result = {31'b0, a < b};
            default:  compare_result = {31'b0, a < b};
        endcase
    end

    // Result multiplexing
    always_comb begin
        case (op)
            ALU_ADD, ALU_SUB:        result = add_sub_result;
            ALU_SLL, ALU_SRL, ALU_SRA: result = shift_result;
            ALU_SLT, ALU_SLTU:       result = compare_result;
            ALU_XOR, ALU_OR, ALU_AND, ALU_PASS: result = logic_result;
            default:                  result = add_sub_result;
        endcase
    end

    // Set flags
    assign zero = (result == 32'b0);
    assign negative = result[31];
    assign overflow = add_sub_overflow;

endmodule 
