import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random

@cocotb.test()
async def test_if_id_reg(dut):
    """Test IF/ID Pipeline Register"""
    if dut._name != "if_id_reg":
        return
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    dut.stall.value = 0
    dut.flush.value = 0
    dut.if_pc.value = 0
    dut.if_instruction.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Extra cycle to ensure reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    
    # Test normal operation
    test_pc = 0x1000
    test_instr = 0x12345678
    
    dut.if_pc.value = test_pc
    dut.if_instruction.value = test_instr
    dut.stall.value = 0
    dut.flush.value = 0
    
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    assert int(dut.id_pc.value) == test_pc, f"PC not propagated correctly. Expected {test_pc}, got {int(dut.id_pc.value)}"
    assert int(dut.id_instruction.value) == test_instr, f"Instruction not propagated correctly"
    
    # Test stall
    new_pc = 0x2000
    new_instr = 0x87654321
    
    dut.if_pc.value = new_pc
    dut.if_instruction.value = new_instr
    dut.stall.value = 1
    
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    assert int(dut.id_pc.value) == test_pc, f"Stall not working for PC"
    assert int(dut.id_instruction.value) == test_instr, f"Stall not working for instruction"
    
    # Test flush
    dut.stall.value = 0
    dut.flush.value = 1
    
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    assert int(dut.id_instruction.value) == 0x00000013, f"Flush not inserting NOP"

@cocotb.test()
async def test_id_ex_reg(dut):
    """Test ID/EX Pipeline Register"""
    if dut._name != "id_ex_reg":
        return
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    dut.flush.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Extra cycle to ensure reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    
    # Test control signals
    dut.id_reg_write.value = 1
    dut.id_alu_src.value = 1
    dut.id_alu_op.value = 0x5
    dut.id_mem_write.value = 0
    dut.id_mem_read.value = 1
    dut.id_mem_size.value = 0x2
    dut.id_branch.value = 0
    dut.id_jump.value = 0
    dut.id_result_src.value = 0x1
    
    # Test data signals
    dut.id_pc.value = 0x1000
    dut.id_rs1_data.value = 0x12345678
    dut.id_rs2_data.value = 0x87654321
    dut.id_imm.value = 0x00000FFF
    dut.id_rs1_addr.value = 0x5
    dut.id_rs2_addr.value = 0xA
    dut.id_rd_addr.value = 0xF
    dut.id_funct3.value = 0x3
    
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    
    # Verify control signals
    assert dut.ex_reg_write.value == 1
    assert dut.ex_alu_src.value == 1
    assert dut.ex_alu_op.value == 0x5
    assert dut.ex_mem_write.value == 0
    assert dut.ex_mem_read.value == 1
    assert dut.ex_mem_size.value == 0x2
    assert dut.ex_branch.value == 0
    assert dut.ex_jump.value == 0
    assert dut.ex_result_src.value == 0x1
    
    # Verify data signals
    assert int(dut.ex_pc.value) == 0x1000
    assert int(dut.ex_rs1_data.value) == 0x12345678
    assert int(dut.ex_rs2_data.value) == 0x87654321
    assert int(dut.ex_imm.value) == 0x00000FFF
    assert int(dut.ex_rd_addr.value) == 0xF
    assert int(dut.ex_funct3.value) == 0x3

@cocotb.test()
async def test_ex_mem_reg(dut):
    """Test EX/MEM Pipeline Register"""
    if dut._name != "ex_mem_reg":
        return
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    dut.flush.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Extra cycle to ensure reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    
    # Test control signals
    dut.ex_reg_write.value = 1
    dut.ex_mem_write.value = 1
    dut.ex_mem_read.value = 0
    dut.ex_mem_size.value = 0x2
    dut.ex_result_src.value = 0x1
    
    # Test data signals
    dut.ex_alu_result.value = 0x12345678
    dut.ex_rs2_data.value = 0x87654321
    dut.ex_rd_addr.value = 0xF
    dut.ex_pc_plus4.value = 0x1004
    
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    
    # Verify control signals
    assert dut.mem_reg_write.value == 1
    assert dut.mem_mem_write.value == 1
    assert dut.mem_mem_size.value == 0x2
    assert dut.mem_result_src.value == 0x1
    
    # Verify data signals
    assert int(dut.mem_alu_result.value) == 0x12345678
    assert int(dut.mem_rs2_data.value) == 0x87654321
    assert int(dut.mem_rd_addr.value) == 0xF
    assert int(dut.mem_pc_plus4.value) == 0x1004

@cocotb.test()
async def test_mem_wb_reg(dut):
    """Test MEM/WB Pipeline Register"""
    if dut._name != "mem_wb_reg":
        return
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Extra cycle to ensure reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    
    # Test control signals
    dut.mem_reg_write.value = 1
    dut.mem_result_src.value = 0x1
    
    # Test data signals
    dut.mem_alu_result.value = 0x12345678
    dut.mem_read_data.value = 0x87654321
    dut.mem_rd_addr.value = 0xF
    dut.mem_pc_plus4.value = 0x1004
    
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait for signals to stabilize
    
    # Verify control signals
    assert dut.wb_reg_write.value == 1
    assert dut.wb_result_src.value == 0x1
    
    # Verify data signals
    assert int(dut.wb_alu_result.value) == 0x12345678
    assert int(dut.wb_read_data.value) == 0x87654321
    assert int(dut.wb_rd_addr.value) == 0xF
    assert int(dut.wb_pc_plus4.value) == 0x1004