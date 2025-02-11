import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
import random
import os
import json

# RISC-V instruction encoding helpers
def encode_r_type(rd, rs1, rs2, funct3, funct7):
    """Encode R-type instruction"""
    return (
        (funct7 << 25) |  # funct7[31:25]
        (rs2 << 20) |    # rs2[24:20]
        (rs1 << 15) |    # rs1[19:15]
        (funct3 << 12) |  # funct3[14:12]
        (rd << 7) |      # rd[11:7]
        0b0110011        # opcode[6:0] for R-type
    )

def encode_i_type(rd, rs1, imm, funct3, opcode):
    """Encode I-type instruction"""
    return (
        ((imm & 0xFFF) << 20) |  # imm[31:20]
        (rs1 << 15) |            # rs1[19:15]
        (funct3 << 12) |         # funct3[14:12]
        (rd << 7) |              # rd[11:7]
        opcode                   # opcode[6:0]
    )

def encode_s_type(rs1, rs2, imm, funct3):
    """Encode S-type instruction"""
    return (
        ((imm & 0xFE0) << 20) |  # imm[31:25]
        (rs2 << 20) |            # rs2[24:20]
        (rs1 << 15) |            # rs1[19:15]
        (funct3 << 12) |         # funct3[14:12]
        ((imm & 0x1F) << 7) |    # imm[11:7]
        0b0100011               # opcode[6:0] for S-type
    )

def encode_b_type(rs1, rs2, imm, funct3):
    """Encode B-type instruction"""
    return (
        ((imm & 0x1000) << 19) |  # imm[31:25]
        ((imm & 0x7E0) << 20) |   # rs2[24:20]
        (rs2 << 20) |             # rs1[19:15]
        (rs1 << 15) |             # funct3[14:12]
        (funct3 << 12) |          # imm[11:7]
        ((imm & 0x1E) << 7) |     # imm[11:7]
        ((imm & 0x800) >> 4) |    # imm[7]
        0b1100011                # opcode[6:0] for B-type
    )

async def initialize_dut(dut):
    """Initialize the DUT and start the clock"""
    # Create a 10ns period clock
    clock = Clock(dut.clk, 10, units="ns")
    # Start the clock
    cocotb.start_soon(clock.start())
    
    # Reset values
    dut.rst_n.value = 0
    
    # Wait 20ns, then release reset
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await Timer(10, units="ns")

@cocotb.test()
async def test_r_type_instructions(dut):
    """Test R-type arithmetic instructions"""
    await initialize_dut(dut)
    
    # Test ADD
    instr = encode_r_type(rd=1, rs1=0, rs2=0, funct3=0b000, funct7=0b0000000)  # add x1, x0, x0
    dut.imem_data.value = instr
    await RisingEdge(dut.clk)
    assert dut.debug_instr.value == instr, "Instruction not properly loaded"
    
    # Test more R-type instructions with different registers and values
    test_cases = [
        # rd, rs1, rs2, funct3, funct7, description
        (2, 0, 0, 0b000, 0b0000000, "add x2, x0, x0"),
        (3, 1, 2, 0b000, 0b0000000, "add x3, x1, x2"),
        (4, 2, 3, 0b000, 0b0100000, "sub x4, x2, x3"),
        (5, 3, 4, 0b111, 0b0000000, "and x5, x3, x4"),
        (6, 4, 5, 0b110, 0b0000000, "or x6, x4, x5"),
        (7, 5, 6, 0b100, 0b0000000, "xor x7, x5, x6")
    ]
    
    for rd, rs1, rs2, funct3, funct7, desc in test_cases:
        instr = encode_r_type(rd, rs1, rs2, funct3, funct7)
        dut.imem_data.value = instr
        await RisingEdge(dut.clk)
        assert dut.debug_instr.value == instr, f"Failed to load instruction: {desc}"

@cocotb.test()
async def test_load_store_instructions(dut):
    """Test load and store instructions"""
    await initialize_dut(dut)
    
    # Store word
    instr = encode_s_type(rs1=0, rs2=1, imm=4, funct3=0b010)  # sw x1, 4(x0)
    dut.imem_data.value = instr
    await RisingEdge(dut.clk)
    assert dut.debug_instr.value == instr, "Store instruction not properly loaded"
    
    # Load word
    instr = encode_i_type(rd=2, rs1=0, imm=4, funct3=0b010, opcode=0b0000011)  # lw x2, 4(x0)
    dut.imem_data.value = instr
    await RisingEdge(dut.clk)
    assert dut.debug_instr.value == instr, "Load instruction not properly loaded"

@cocotb.test()
async def test_branch_instructions(dut):
    """Test branch instructions"""
    await initialize_dut(dut)
    
    # Test branch equal
    instr = encode_b_type(rs1=1, rs2=2, imm=8, funct3=0b000)  # beq x1, x2, 8
    dut.imem_data.value = instr
    await RisingEdge(dut.clk)
    assert dut.debug_instr.value == instr, "Branch instruction not properly loaded"
    
    # Test branch not equal
    instr = encode_b_type(rs1=3, rs2=4, imm=-8, funct3=0b001)  # bne x3, x4, -8
    dut.imem_data.value = instr
    await RisingEdge(dut.clk)
    assert dut.debug_instr.value == instr, "Branch instruction not properly loaded"

@cocotb.test()
async def test_immediate_instructions(dut):
    """Test immediate arithmetic instructions"""
    await initialize_dut(dut)
    
    # Test ADDI
    instr = encode_i_type(rd=1, rs1=0, imm=5, funct3=0b000, opcode=0b0010011)  # addi x1, x0, 5
    dut.imem_data.value = instr
    await RisingEdge(dut.clk)
    assert dut.debug_instr.value == instr, "ADDI instruction not properly loaded"
    
    # Test more immediate instructions
    test_cases = [
        # rd, rs1, imm, funct3, description
        (2, 1, 3, 0b000, "addi x2, x1, 3"),
        (3, 2, -5, 0b000, "addi x3, x2, -5"),
        (4, 3, 0xFF, 0b100, "xori x4, x3, 0xFF"),
        (5, 4, 0x0F, 0b110, "ori x5, x4, 0x0F"),
        (6, 5, 0xF0, 0b111, "andi x6, x5, 0xF0")
    ]
    
    for rd, rs1, imm, funct3, desc in test_cases:
        instr = encode_i_type(rd, rs1, imm, funct3, opcode=0b0010011)
        dut.imem_data.value = instr
        await RisingEdge(dut.clk)
        assert dut.debug_instr.value == instr, f"Failed to load instruction: {desc}"

@cocotb.test()
async def test_memory_data_patterns(dut):
    """Test memory operations with various data patterns"""
    await initialize_dut(dut)
    
    # Test word access
    test_data = [
        0x12345678,
        0xFFFFFFFF,
        0x00000000,
        0xAAAAAAAA,
        0x55555555
    ]
    
    for i, data in enumerate(test_data):
        # Store word
        dut.dmem_wdata.value = data
        dut.dmem_addr.value = i * 4
        dut.dmem_we.value = 1
        dut.dmem_be.value = 0xF
        await RisingEdge(dut.clk)
        
        # Verify stored data
        dut.dmem_we.value = 0
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")  # Wait for read to complete
        assert dut.dmem_rdata.value == data, f"Memory data mismatch at address {i*4}" 