// ALU for RISC-V RV32I CPU
// Implements all arithmetic and logical operations from the RV32I ISA

module alu (
    input  logic [31:0] a,          // First operand
    input  logic [31:0] b,          // Second operand
    input  logic [3:0]  op,         // Operation to perform
    output logic [31:0] result,     // Result of operation
    output logic        zero,       // Result is zero
    output logic        negative,   // Result is negative
    output logic        overflow    // Overflow occurred
);

    // Internal signals for arithmetic operations
    logic [31:0] add_result;
    logic [31:0] sub_result;
    logic [31:0] and_result;
    logic [31:0] or_result;
    logic [31:0] xor_result;
    logic [31:0] slt_result;
    logic [31:0] sltu_result;
    logic [31:0] sll_result;
    logic [31:0] srl_result;
    logic [31:0] sra_result;

    // Operation results
    assign add_result = a + b;
    assign sub_result = a - b;
    assign and_result = a & b;
    assign or_result = a | b;
    assign xor_result = a ^ b;
    assign slt_result = {31'b0, $signed(a) < $signed(b)};
    assign sltu_result = {31'b0, a < b};
    assign sll_result = a << b[4:0];
    assign srl_result = a >> b[4:0];
    assign sra_result = $signed(a) >>> b[4:0];

    // Result selection using case statement
    always_comb begin
        case (op)
            4'b0000: result = add_result;  // ADD
            4'b1000: result = sub_result;  // SUB
            4'b0111: result = and_result;  // AND
            4'b0110: result = or_result;   // OR
            4'b0100: result = xor_result;  // XOR
            4'b0010: result = slt_result;  // SLT
            4'b0011: result = sltu_result; // SLTU
            4'b0001: result = sll_result;  // SLL
            4'b0101: result = srl_result;  // SRL
            4'b1101: result = sra_result;  // SRA
            default: result = 32'b0;
        endcase
    end

    // Status flags
    assign zero = (result == 32'b0);
    assign negative = result[31];
    assign overflow = ((op == 4'b0000) && (a[31] == b[31]) && (result[31] != a[31])) || // ADD overflow
                     ((op == 4'b1000) && (a[31] != b[31]) && (result[31] == b[31]));   // SUB overflow

endmodule 
