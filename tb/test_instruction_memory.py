import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from collections import defaultdict
import json
import atexit
import random

# Coverage tracking
class CoverageCollector:
    def __init__(self):
        self.access_patterns = defaultdict(int)  # Track memory access patterns
        self.special_cases = defaultdict(int)    # Track special cases
        self.boundary_cases = defaultdict(int)   # Track boundary conditions
        
        # Coverage goals
        self.goals = {
            "access_patterns": {
                "sequential": 10,     # Sequential access
                "random": 10,         # Random access
                "word_aligned": 10,   # Word-aligned access
                "unaligned": 5        # Unaligned access attempts
            },
            "special_cases": {
                "nop_read": 5,        # Reading NOP instructions
                "reset_access": 5,    # Access after reset
                "repeated_access": 5   # Multiple reads from same address
            },
            "boundary_cases": {
                "start_address": 5,   # Access at start of memory
                "end_address": 5,     # Access at end of memory
                "out_of_bounds": 5    # Access beyond memory bounds
            }
        }

    def report(self):
        """Generate and print coverage report"""
        cocotb.log.info("Instruction Memory Coverage Report:")
        cocotb.log.info("=================================")
        
        total_points = 0
        covered_points = 0
        
        # Access patterns coverage
        cocotb.log.info("\nAccess Patterns Coverage:")
        for pattern, count in sorted(self.access_patterns.items()):
            total_points += 1
            if count >= self.goals["access_patterns"].get(pattern, 0):
                covered_points += 1
            cocotb.log.info(f"  {pattern}: {count} occurrences (goal: {self.goals['access_patterns'].get(pattern, 0)})")
        
        # Special cases coverage
        cocotb.log.info("\nSpecial Cases Coverage:")
        for case, count in sorted(self.special_cases.items()):
            total_points += 1
            if count >= self.goals["special_cases"].get(case, 0):
                covered_points += 1
            cocotb.log.info(f"  {case}: {count} occurrences (goal: {self.goals['special_cases'].get(case, 0)})")
        
        # Boundary cases coverage
        cocotb.log.info("\nBoundary Cases Coverage:")
        for case, count in sorted(self.boundary_cases.items()):
            total_points += 1
            if count >= self.goals["boundary_cases"].get(case, 0):
                covered_points += 1
            cocotb.log.info(f"  {case}: {count} occurrences (goal: {self.goals['boundary_cases'].get(case, 0)})")
        
        # Overall coverage
        coverage_percentage = (covered_points / total_points) * 100 if total_points > 0 else 0
        cocotb.log.info(f"\nOverall Coverage: {coverage_percentage:.2f}% ({covered_points}/{total_points} points)")
        
        # Save coverage data to file
        coverage_data = {
            "access_patterns": dict(self.access_patterns),
            "special_cases": dict(self.special_cases),
            "boundary_cases": dict(self.boundary_cases),
            "coverage_percentage": coverage_percentage,
            "covered_points": covered_points,
            "total_points": total_points
        }
        
        with open("coverage_instruction_memory.json", "w") as f:
            json.dump(coverage_data, f, indent=4)

# Global coverage collector
coverage = CoverageCollector()

# Register coverage report to run at exit
@atexit.register
def save_coverage():
    coverage.report()

async def initialize_dut(dut):
    """Initialize the DUT and start the clock."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize address to 0 (word-aligned)
    dut.addr.value = 0
    coverage.special_cases["reset_access"] += 1
    
    # Wait a few clock cycles
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_initial_values(dut):
    """Test that memory is initialized with NOP instructions."""
    await initialize_dut(dut)
    
    # Check first few addresses contain NOP instructions
    for addr in range(0, 32, 4):  # Increased range to check more NOPs
        dut.addr.value = addr
        if addr == 0:
            coverage.boundary_cases["start_address"] += 1
        coverage.access_patterns["sequential"] += 1
        coverage.special_cases["nop_read"] += 1
        
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert dut.rdata.value == 0x00000013, \
            f"Memory at {addr} should be NOP (0x00000013), got {dut.rdata.value:08x}"

@cocotb.test()
async def test_word_alignment(dut):
    """Test memory access with non-word-aligned addresses."""
    await initialize_dut(dut)
    
    # Try accessing with non-aligned addresses
    for base_addr in [0x0, 0x100, 0x200, 0x300]:  # Test across memory range
        for offset in [1, 2, 3]:
            addr = base_addr + offset
            dut.addr.value = addr
            coverage.access_patterns["unaligned"] += 1
            
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            # The actual data should still be aligned (bottom bits ignored)
            expected_aligned_addr = addr & ~0x3
            assert dut.rdata.value == 0x00000013, \
                f"Memory access with non-aligned address {addr} should still return NOP"

@cocotb.test()
async def test_sequential_access(dut):
    """Test sequential memory access."""
    await initialize_dut(dut)
    
    # Test multiple sequential access patterns
    for base_addr in [0x0, 0x100, 0x200, 0x300]:
        for offset in range(0, 32, 4):
            addr = base_addr + offset
            dut.addr.value = addr
            coverage.access_patterns["sequential"] += 1
            coverage.access_patterns["word_aligned"] += 1
            if addr == 0:
                coverage.boundary_cases["start_address"] += 1
            
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            assert dut.rdata.value == 0x00000013, \
                f"Sequential access at {addr} failed"

@cocotb.test()
async def test_memory_bounds(dut):
    """Test memory access at boundary conditions."""
    await initialize_dut(dut)
    
    # Test near the end of memory with multiple addresses
    end_addresses = [
        1024 - 4,  # Last valid word
        1024 - 8,  # Second to last word
        1024 - 12, # Third to last word
        1024 - 16  # Fourth to last word
    ]
    
    for addr in end_addresses:
        dut.addr.value = addr
        coverage.boundary_cases["end_address"] += 1
        coverage.access_patterns["word_aligned"] += 1
        
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert dut.rdata.value == 0x00000013, \
            f"Access at near-end address {addr} failed"
    
    # Test multiple out-of-bounds addresses
    for addr in [1024, 1028, 1032, 2048]:
        dut.addr.value = addr
        coverage.boundary_cases["out_of_bounds"] += 1
        
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

@cocotb.test()
async def test_repeated_access(dut):
    """Test repeated access to same address."""
    await initialize_dut(dut)
    
    # Test repeated access at multiple addresses
    test_addresses = [0x0, 0x20, 0x100, 0x3FC]  # Including start and near-end addresses
    for test_addr in test_addresses:
        for _ in range(3):
            dut.addr.value = test_addr
            coverage.special_cases["repeated_access"] += 1
            coverage.access_patterns["word_aligned"] += 1
            if test_addr == 0:
                coverage.boundary_cases["start_address"] += 1
            if test_addr == 0x3FC:
                coverage.boundary_cases["end_address"] += 1
            
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            assert dut.rdata.value == 0x00000013, \
                f"Repeated access at {test_addr} failed"

@cocotb.test()
async def test_random_access(dut):
    """Test random access patterns."""
    await initialize_dut(dut)
    
    # Generate random word-aligned addresses
    for _ in range(20):
        # Generate word-aligned address (multiple of 4)
        addr = random.randrange(0, 1024, 4)
        dut.addr.value = addr
        coverage.access_patterns["random"] += 1
        coverage.access_patterns["word_aligned"] += 1
        coverage.special_cases["nop_read"] += 1
        
        if addr == 0:
            coverage.boundary_cases["start_address"] += 1
        if addr >= 1020:  # Last valid word address
            coverage.boundary_cases["end_address"] += 1
        
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert dut.rdata.value == 0x00000013, \
            f"Random access at {addr} failed" 