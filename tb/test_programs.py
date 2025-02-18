import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from program_loader import ProgramLoader, create_test_program
import os
from cocotb.binary import BinaryValue

# Memory base addresses
IMEM_BASE = 0x00000000
DMEM_BASE = 0x00001000

async def initialize_dut(dut):
    """Initialize the DUT and start the clock."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await Timer(10, units="ns")
    
    # Initialize memory arrays if they don't exist
    if not hasattr(dut.imem, 'mem'):
        dut.imem.mem = []
        for i in range(1024):
            dut.imem.mem.append(BinaryValue(value=0, n_bits=32))
    
    if not hasattr(dut.dmem, 'mem'):
        dut.dmem.mem = []
        for i in range(1024):
            dut.dmem.mem.append(BinaryValue(value=0, n_bits=8))

async def load_program(dut, program):
    """Load a program into instruction memory."""
    # Load program into instruction memory
    for i, instr in enumerate(program):
        dut.imem.mem[i].value = instr
        await Timer(1, units="ns")  # Allow time for value to settle

async def read_memory(dut, addr):
    """Read a word from data memory."""
    if addr < DMEM_BASE or addr >= DMEM_BASE + 4096:
        raise ValueError(f"Invalid memory address: {hex(addr)}")
    word_addr = (addr - DMEM_BASE) >> 2
    byte_addr = word_addr << 2
    
    # Read four bytes and combine them
    value = (int(dut.dmem.mem[byte_addr + 3].value) << 24 |
            int(dut.dmem.mem[byte_addr + 2].value) << 16 |
            int(dut.dmem.mem[byte_addr + 1].value) << 8 |
            int(dut.dmem.mem[byte_addr].value))
    return value

async def write_memory(dut, addr, data):
    """Write a word to data memory."""
    if addr < DMEM_BASE or addr >= DMEM_BASE + 4096:
        raise ValueError(f"Invalid memory address: {hex(addr)}")
    word_addr = (addr - DMEM_BASE) >> 2
    byte_addr = word_addr << 2
    
    # Write individual bytes
    dut.dmem.mem[byte_addr].value = data & 0xFF
    dut.dmem.mem[byte_addr + 1].value = (data >> 8) & 0xFF
    dut.dmem.mem[byte_addr + 2].value = (data >> 16) & 0xFF
    dut.dmem.mem[byte_addr + 3].value = (data >> 24) & 0xFF
    await Timer(1, units="ns")  # Allow time for values to settle

@cocotb.test()
async def test_fibonacci(dut):
    """Test the Fibonacci program."""
    # Create programs directory if it doesn't exist
    os.makedirs("tb/programs", exist_ok=True)
    
    # Create Fibonacci program if it doesn't exist
    fib_file = "tb/programs/fibonacci.s"
    if not os.path.exists(fib_file):
        with open(fib_file, 'w') as f:
            f.write("""# Fibonacci sequence calculator
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
    sw x3, 0(x4)
    
    # Store first two numbers
    sw x1, 4(x4)      # Store F0
    sw x2, 8(x4)      # Store F1
    addi x4, x4, 8    # Point to next storage location
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
""")
    
    loader = ProgramLoader()
    program = loader.assemble_and_load(fib_file)
    
    # Initialize and load program
    await initialize_dut(dut)
    await load_program(dut, program)
    
    # Initialize data memory
    await write_memory(dut, DMEM_BASE, 0)  # Clear number of elements
    
    # Run until completion (100 cycles should be enough)
    for _ in range(100):
        await RisingEdge(dut.clk)
    
    # Check results
    num_elements = await read_memory(dut, DMEM_BASE)
    assert num_elements == 10, f"Expected 10 elements, got {num_elements}"
    
    # Read and verify Fibonacci sequence
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    for i, expected_val in enumerate(expected):
        val = await read_memory(dut, DMEM_BASE + 4 + i*4)
        assert val == expected_val, f"Mismatch at index {i}: expected {expected_val}, got {val}"

@cocotb.test()
async def test_custom_program(dut):
    """Test a custom program."""
    # Simple program to add numbers and store result
    instructions = [
        "li x4, 0x1000",     # Load data memory base address
        "addi x1, x0, 10",   # x1 = 10
        "addi x2, x0, 20",   # x2 = 20
        "add x3, x1, x2",    # x3 = x1 + x2
        "sw x3, 0(x4)"       # Store result at base address
    ]
    
    # Create and load program
    test_file = create_test_program(instructions)
    loader = ProgramLoader()
    program = loader.assemble_and_load(test_file)
    
    # Initialize and load program
    await initialize_dut(dut)
    await load_program(dut, program)
    
    # Initialize data memory
    await write_memory(dut, DMEM_BASE, 0)
    
    # Run for a few cycles
    for _ in range(10):
        await RisingEdge(dut.clk)
    
    # Check result
    result = await read_memory(dut, DMEM_BASE)
    assert result == 30, f"Expected 30, got {result}" 