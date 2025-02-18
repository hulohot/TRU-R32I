# Fibonacci sequence calculator
# Calculates first 10 Fibonacci numbers and stores them in memory
# Memory layout:
# 0x1000: Number of elements (10)
# 0x1004-0x1028: Fibonacci sequence

.section .text
.globl _start

_start:
    # Initialize registers
    li x1, 0          # First number (F0)
    li x2, 1          # Second number (F1)
    li x3, 10         # Counter (calculate 10 numbers)
    li x4, 0x1000     # Base address for storing results
    
    # Store number of elements
    sw x3, 0(x4)      # Store count at 0x1000
    
    # Store first two numbers
    sw x1, 4(x4)      # Store F0 at 0x1004
    sw x2, 8(x4)      # Store F1 at 0x1008
    addi x4, x4, 8    # Point to next storage location (0x1008)
    addi x3, x3, -2   # Decrement counter by 2 (already stored 2 numbers)
    
loop:
    beqz x3, done     # If counter is zero, we're done
    add x5, x1, x2    # Calculate next Fibonacci number
    mv x1, x2         # Shift numbers: x1 = x2
    mv x2, x5         # x2 = new number
    addi x4, x4, 4    # Point to next storage location
    sw x5, 0(x4)      # Store the number
    addi x3, x3, -1   # Decrement counter
    j loop            # Continue loop
    
done:
    # Program completed
    nop 