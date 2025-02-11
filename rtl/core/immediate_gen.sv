module immediate_gen (
    input  logic [31:7] instruction,   // Instruction bits [31:7]
    output logic [31:0] i_type,        // I-type immediate
    output logic [31:0] s_type,        // S-type immediate
    output logic [31:0] b_type,        // B-type immediate
    output logic [31:0] u_type,        // U-type immediate
    output logic [31:0] j_type         // J-type immediate
);

    // I-type immediate: sign-extended 12-bit immediate
    assign i_type = {{20{instruction[31]}}, instruction[31:20]};
    
    // S-type immediate: sign-extended 12-bit immediate from scattered fields
    assign s_type = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]};
    
    // B-type immediate: sign-extended 13-bit immediate from scattered fields
    assign b_type = {{19{instruction[31]}}, instruction[31], instruction[7], 
                    instruction[30:25], instruction[11:8], 1'b0};
    
    // U-type immediate: 20-bit upper immediate
    assign u_type = {instruction[31:12], 12'b0};
    
    // J-type immediate: sign-extended 21-bit immediate from scattered fields
    assign j_type = {{11{instruction[31]}}, instruction[31], instruction[19:12],
                    instruction[20], instruction[30:21], 1'b0};

endmodule 
