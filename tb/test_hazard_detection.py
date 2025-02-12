import cocotb
from cocotb.triggers import Timer
import random

@cocotb.test()
async def test_no_hazard(dut):
    """Test case where no hazards are present"""
    
    # Set up non-hazardous instruction sequence
    dut.id_rs1_addr.value = 1
    dut.id_rs2_addr.value = 2
    dut.ex_rd_addr.value = 3
    dut.mem_rd_addr.value = 4
    dut.id_branch.value = 0
    dut.id_jump.value = 0
    dut.ex_mem_read.value = 0
    dut.ex_branch_taken.value = 0
    dut.ex_reg_write.value = 1
    dut.mem_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.stall_if.value == 0, "No stall should occur without hazards"
    assert dut.stall_id.value == 0, "No stall should occur without hazards"
    assert dut.flush_if.value == 0, "No flush should occur without hazards"
    assert dut.flush_id.value == 0, "No flush should occur without hazards"
    assert dut.flush_ex.value == 0, "No flush should occur without hazards"

@cocotb.test()
async def test_load_use_hazard(dut):
    """Test detection of load-use hazards"""
    
    # Set up load-use hazard (EX stage load followed by dependent instruction)
    dut.id_rs1_addr.value = 5
    dut.ex_rd_addr.value = 5
    dut.ex_mem_read.value = 1
    dut.ex_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.stall_if.value == 1, "IF stage should stall on load-use hazard"
    assert dut.stall_id.value == 1, "ID stage should stall on load-use hazard"
    assert dut.flush_ex.value == 1, "EX stage should be flushed on load-use hazard"
    
    # Test with rs2 dependency
    dut.id_rs1_addr.value = 1
    dut.id_rs2_addr.value = 5
    
    await Timer(1, units="ns")
    assert dut.stall_if.value == 1, "IF stage should stall on load-use hazard (rs2)"
    assert dut.stall_id.value == 1, "ID stage should stall on load-use hazard (rs2)"
    assert dut.flush_ex.value == 1, "EX stage should be flushed on load-use hazard (rs2)"

@cocotb.test()
async def test_branch_hazard(dut):
    """Test detection of control hazards from branches"""
    
    # Set up branch instruction
    dut.id_branch.value = 1
    dut.ex_branch_taken.value = 1
    
    await Timer(1, units="ns")
    assert dut.flush_if.value == 1, "IF stage should be flushed on taken branch"
    assert dut.flush_id.value == 1, "ID stage should be flushed on taken branch"
    assert dut.flush_ex.value == 1, "EX stage should be flushed on taken branch"
    
    # Test not taken branch
    dut.ex_branch_taken.value = 0
    
    await Timer(1, units="ns")
    assert dut.flush_if.value == 0, "No flush should occur on not-taken branch"
    assert dut.flush_id.value == 0, "No flush should occur on not-taken branch"
    assert dut.flush_ex.value == 0, "No flush should occur on not-taken branch"

@cocotb.test()
async def test_jump_hazard(dut):
    """Test detection of control hazards from jumps"""
    
    # Set up jump instruction
    dut.id_jump.value = 1
    
    await Timer(1, units="ns")
    assert dut.flush_if.value == 1, "IF stage should be flushed on jump"
    assert dut.flush_id.value == 1, "ID stage should be flushed on jump"
    assert dut.flush_ex.value == 1, "EX stage should be flushed on jump"

@cocotb.test()
async def test_multiple_hazards(dut):
    """Test handling of multiple simultaneous hazards"""
    
    # Set up both load-use and branch hazards
    dut.id_rs1_addr.value = 6
    dut.ex_rd_addr.value = 6
    dut.ex_mem_read.value = 1
    dut.ex_reg_write.value = 1
    dut.id_branch.value = 1
    dut.ex_branch_taken.value = 1
    
    await Timer(1, units="ns")
    assert dut.stall_if.value == 1, "Load-use hazard should take precedence"
    assert dut.stall_id.value == 1, "Load-use hazard should take precedence"
    assert dut.flush_ex.value == 1, "EX stage should be flushed"

@cocotb.test()
async def test_x0_hazards(dut):
    """Test that hazards are not detected for register x0"""
    
    # Set up potential load-use hazard with x0
    dut.id_rs1_addr.value = 0
    dut.id_rs2_addr.value = 0
    dut.ex_rd_addr.value = 0
    dut.ex_mem_read.value = 1
    dut.ex_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.stall_if.value == 0, "No hazard should be detected for x0"
    assert dut.stall_id.value == 0, "No hazard should be detected for x0"
    assert dut.flush_ex.value == 0, "No hazard should be detected for x0" 