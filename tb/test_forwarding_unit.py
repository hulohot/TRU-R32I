import cocotb
from cocotb.triggers import Timer
import random

@cocotb.test()
async def test_no_forwarding(dut):
    """Test case where no forwarding is needed"""
    
    # Set source registers that don't match any destination
    dut.ex_rs1_addr.value = 1
    dut.ex_rs2_addr.value = 2
    dut.mem_rd_addr.value = 3
    dut.wb_rd_addr.value = 4
    dut.mem_reg_write.value = 1
    dut.wb_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 0, "Forward A should be 0 when no forwarding needed"
    assert dut.forward_b.value == 0, "Forward B should be 0 when no forwarding needed"

@cocotb.test()
async def test_mem_forwarding(dut):
    """Test forwarding from MEM stage"""
    
    # Test forwarding for rs1
    dut.ex_rs1_addr.value = 5
    dut.ex_rs2_addr.value = 2
    dut.mem_rd_addr.value = 5
    dut.wb_rd_addr.value = 4
    dut.mem_reg_write.value = 1
    dut.wb_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 1, "Forward A should be 1 for MEM forwarding"
    assert dut.forward_b.value == 0, "Forward B should be 0 when no forwarding needed"
    
    # Test forwarding for rs2
    dut.ex_rs1_addr.value = 1
    dut.ex_rs2_addr.value = 5
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 0, "Forward A should be 0 when no forwarding needed"
    assert dut.forward_b.value == 1, "Forward B should be 1 for MEM forwarding"

@cocotb.test()
async def test_wb_forwarding(dut):
    """Test forwarding from WB stage"""
    
    # Test forwarding for rs1
    dut.ex_rs1_addr.value = 6
    dut.ex_rs2_addr.value = 2
    dut.mem_rd_addr.value = 3
    dut.wb_rd_addr.value = 6
    dut.mem_reg_write.value = 1
    dut.wb_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 2, "Forward A should be 2 for WB forwarding"
    assert dut.forward_b.value == 0, "Forward B should be 0 when no forwarding needed"
    
    # Test forwarding for rs2
    dut.ex_rs1_addr.value = 1
    dut.ex_rs2_addr.value = 6
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 0, "Forward A should be 0 when no forwarding needed"
    assert dut.forward_b.value == 2, "Forward B should be 2 for WB forwarding"

@cocotb.test()
async def test_mem_priority(dut):
    """Test that MEM stage forwarding has priority over WB stage"""
    
    # Set up conflict where both MEM and WB could forward
    dut.ex_rs1_addr.value = 7
    dut.mem_rd_addr.value = 7
    dut.wb_rd_addr.value = 7
    dut.mem_reg_write.value = 1
    dut.wb_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 1, "MEM forwarding should have priority over WB"

@cocotb.test()
async def test_reg_write_disabled(dut):
    """Test that forwarding doesn't occur when reg_write is disabled"""
    
    # Set up potential forwarding but with reg_write disabled
    dut.ex_rs1_addr.value = 8
    dut.mem_rd_addr.value = 8
    dut.mem_reg_write.value = 0
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 0, "No forwarding should occur when reg_write is disabled"

@cocotb.test()
async def test_x0_forwarding(dut):
    """Test that forwarding doesn't occur for register x0"""
    
    # Try to forward to/from x0
    dut.ex_rs1_addr.value = 0
    dut.ex_rs2_addr.value = 1
    dut.mem_rd_addr.value = 0
    dut.wb_rd_addr.value = 0
    dut.mem_reg_write.value = 1
    dut.wb_reg_write.value = 1
    
    await Timer(1, units="ns")
    assert dut.forward_a.value == 0, "No forwarding should occur for x0"
    assert dut.forward_b.value == 0, "No forwarding should occur when not needed" 