# Simple test program for RISC-V CPU
# Tests basic arithmetic, memory and control flow operations

.section .text
.globl _start

_start:
    # Initialize registers
    li x1, 10        # Load immediate value 10 into x1
    li x2, 20        # Load immediate value 20 into x2
    
    # Test arithmetic
    add x3, x1, x2   # x3 = x1 + x2 (should be 30)
    sub x4, x2, x1   # x4 = x2 - x1 (should be 10)
    
    # Test memory operations
    sw x3, 0(x0)     # Store x3 to memory address 0
    lw x5, 0(x0)     # Load from memory address 0 into x5 (should be 30)
    
    # Test branching
    beq x3, x5, pass # Branch if x3 equals x5 (should be taken)
    j fail           # Should not reach here
    
pass:
    nop             # Test completion marker
    j pass          # Infinite loop on success

fail:
    li x1, -1       # Load -1 to indicate failure
    j fail          # Infinite loop on failure 