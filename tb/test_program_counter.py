import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ClockCycles
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from collections import defaultdict
import json
import atexit

# Coverage tracking
class CoverageCollector:
    def __init__(self):
        self.operations = defaultdict(int)     # Track PC operations
        self.transitions = defaultdict(int)    # Track state transitions
        self.addresses = defaultdict(int)      # Track address ranges
        
        # Coverage goals
        self.goals = {
            "operations": {
                "reset": 5,          # Reset operation
                "increment": 10,     # Normal increment
                "stall": 5,         # Stall operation
                "branch": 10,        # Branch operation
                "branch_stall": 5    # Branch followed by stall
            },
            "transitions": {
                "reset_to_increment": 5,   # From reset to normal increment
                "increment_to_stall": 5,   # From increment to stall
                "stall_to_increment": 5,   # From stall back to increment
                "increment_to_branch": 5,  # From increment to branch
                "branch_to_increment": 5   # From branch back to increment
            },
            "addresses": {
                "zero": 5,           # Zero address
                "word_aligned": 10,  # Word-aligned addresses
                "near_max": 5,       # Near maximum value
                "sequential": 10,    # Sequential addresses
                "branch_target": 5   # Branch target addresses
            }
        }

    def report(self):
        """Generate and print coverage report"""
        cocotb.log.info("Program Counter Coverage Report:")
        cocotb.log.info("================================")
        
        total_points = 0
        covered_points = 0
        
        # Operations coverage
        cocotb.log.info("\nOperations Coverage:")
        for op, count in sorted(self.operations.items()):
            total_points += 1
            if count >= self.goals["operations"].get(op, 0):
                covered_points += 1
            cocotb.log.info(f"  {op}: {count} occurrences (goal: {self.goals['operations'].get(op, 0)})")
        
        # Transitions coverage
        cocotb.log.info("\nTransitions Coverage:")
        for trans, count in sorted(self.transitions.items()):
            total_points += 1
            if count >= self.goals["transitions"].get(trans, 0):
                covered_points += 1
            cocotb.log.info(f"  {trans}: {count} occurrences (goal: {self.goals['transitions'].get(trans, 0)})")
        
        # Addresses coverage
        cocotb.log.info("\nAddresses Coverage:")
        for addr, count in sorted(self.addresses.items()):
            total_points += 1
            if count >= self.goals["addresses"].get(addr, 0):
                covered_points += 1
            cocotb.log.info(f"  {addr}: {count} occurrences (goal: {self.goals['addresses'].get(addr, 0)})")
        
        # Overall coverage
        coverage_percentage = (covered_points / total_points) * 100 if total_points > 0 else 0
        cocotb.log.info(f"\nOverall Coverage: {coverage_percentage:.2f}% ({covered_points}/{total_points} points)")
        
        # Save coverage data to file
        coverage_data = {
            "operations": dict(self.operations),
            "transitions": dict(self.transitions),
            "addresses": dict(self.addresses),
            "coverage_percentage": coverage_percentage,
            "covered_points": covered_points,
            "total_points": total_points
        }
        
        with open("coverage_program_counter.json", "w") as f:
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
    
    # Initialize inputs
    dut.rst_n.value = 0
    dut.stall.value = 0
    dut.branch_taken.value = 0
    dut.branch_target.value = 0
    
    coverage.operations["reset"] += 1
    coverage.addresses["zero"] += 1
    
    # Wait a few clock cycles in reset
    await Timer(20, units="ns")
    
    # Release reset and wait one more cycle
    dut.rst_n.value = 1
    coverage.transitions["reset_to_increment"] += 1
    await Timer(10, units="ns")

@cocotb.test()
async def test_reset(dut):
    """Test reset behavior."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize in reset
    dut.rst_n.value = 0
    dut.stall.value = 0
    dut.branch_taken.value = 0
    dut.branch_target.value = 0
    
    coverage.operations["reset"] += 1
    coverage.addresses["zero"] += 1
    
    # Wait a few cycles
    await Timer(20, units="ns")
    
    # Check values in reset
    assert dut.pc.value == 0, f"PC should be 0 in reset, got {dut.pc.value}"
    
    # Release reset
    dut.rst_n.value = 1
    coverage.transitions["reset_to_increment"] += 1
    await Timer(20, units="ns")
    
    # Check PC increments after reset
    assert dut.pc.value == 8, f"PC should be 8 after reset, got {dut.pc.value}"
    coverage.operations["increment"] += 1
    coverage.addresses["word_aligned"] += 1

@cocotb.test()
async def test_sequential_increment(dut):
    """Test normal sequential instruction fetching."""
    await initialize_dut(dut)
    await Timer(10, units="ns")
    
    # Check several cycles of sequential increment
    expected_pc = 8  # After initialize_dut, we should be at 8
    for _ in range(5):
        assert dut.pc.value == expected_pc, f"PC should be {expected_pc}, got {dut.pc.value}"
        coverage.operations["increment"] += 1
        coverage.addresses["sequential"] += 1
        coverage.addresses["word_aligned"] += 1
        await Timer(10, units="ns")
        expected_pc += 4

@cocotb.test()
async def test_stall(dut):
    """Test stall behavior."""
    await initialize_dut(dut)
    await Timer(10, units="ns")
    
    # Get current PC value
    current_pc = dut.pc.value
    
    # Assert stall
    dut.stall.value = 1
    coverage.operations["stall"] += 1
    coverage.transitions["increment_to_stall"] += 1
    await Timer(30, units="ns")
    
    # Verify PC hasn't changed
    assert dut.pc.value == current_pc, f"PC should not change while stalled"
    
    # Release stall
    dut.stall.value = 0
    coverage.transitions["stall_to_increment"] += 1
    await Timer(10, units="ns")
    
    # Verify PC continues from where it was
    assert dut.pc.value == current_pc + 4, f"PC should increment after stall is released"
    coverage.operations["increment"] += 1

@cocotb.test()
async def test_branch(dut):
    """Test branch behavior."""
    await initialize_dut(dut)
    await Timer(10, units="ns")
    
    # Take a branch
    branch_target = 0x1000
    dut.branch_taken.value = 1
    dut.branch_target.value = branch_target
    coverage.operations["branch"] += 1
    coverage.transitions["increment_to_branch"] += 1
    coverage.addresses["branch_target"] += 1
    
    await Timer(10, units="ns")
    
    # Verify branch was taken
    assert dut.pc.value == branch_target, f"PC should be branch target after branch taken"
    
    # Return to sequential execution
    dut.branch_taken.value = 0
    coverage.transitions["branch_to_increment"] += 1
    await Timer(10, units="ns")
    
    # Verify normal increment after branch
    assert dut.pc.value == branch_target + 4, f"PC should increment normally after branch"
    coverage.operations["increment"] += 1

@cocotb.test()
async def test_branch_edge_cases(dut):
    """Test branch behavior with edge cases."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize coverage
    coverage.operations["reset"] += 1
    
    # Reset
    await initialize_dut(dut)
    await ClockCycles(dut.clk, 1)  # Wait for reset to take effect
    
    # Test branch to near-max address
    max_addr = (1 << 32) - 8  # Near maximum 32-bit value, word-aligned
    dut.branch_target.value = max_addr
    dut.branch_taken.value = 1
    await ClockCycles(dut.clk, 2)  # Wait for branch to take effect
    assert dut.pc.value == max_addr
    coverage.operations["branch"] += 1
    coverage.addresses["near_max"] += 1
    coverage.transitions["increment_to_branch"] += 1
    
    # Test branch with stall
    branch_addr = 0x1000
    dut.branch_target.value = branch_addr
    dut.stall.value = 1
    await ClockCycles(dut.clk, 2)  # Wait for stall to take effect
    assert dut.pc.value == max_addr  # Should maintain current PC during stall
    coverage.operations["branch_stall"] += 1
    
    # Release stall and complete branch
    dut.stall.value = 0
    await ClockCycles(dut.clk, 2)  # Wait for branch to complete
    assert dut.pc.value == branch_addr
    coverage.operations["branch"] += 1
    coverage.transitions["branch_to_increment"] += 1

@cocotb.test()
async def test_multiple_branches(dut):
    """Test multiple branch operations."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize coverage
    coverage.operations["reset"] += 1
    
    # Reset
    await initialize_dut(dut)
    await ClockCycles(dut.clk, 1)  # Wait for reset to take effect
    
    # Test multiple branches with different patterns
    branch_targets = [
        0x4,        # Word-aligned
        0x1000,     # Word-aligned, mid-range
        0x7FFFFFC,  # Near max
        0x100,      # Another word-aligned
        0x2000      # Word-aligned, different range
    ]
    
    for target in branch_targets:
        # Normal branch
        dut.branch_target.value = target
        dut.branch_taken.value = 1
        await ClockCycles(dut.clk, 2)  # Wait for branch to take effect
        assert dut.pc.value == target
        coverage.operations["branch"] += 1
        coverage.addresses["word_aligned"] += 1
        coverage.transitions["increment_to_branch"] += 1
        
        # Sequential execution after branch
        dut.branch_taken.value = 0
        await ClockCycles(dut.clk, 1)  # Wait for sequential execution
        expected_pc = target + 4  # PC increments by 4 each cycle
        assert dut.pc.value == expected_pc
        coverage.addresses["sequential"] += 1
        coverage.operations["increment"] += 1
        coverage.transitions["branch_to_increment"] += 1
        
        # Branch with stall
        next_target = target + 0x1000
        dut.branch_target.value = next_target
        dut.branch_taken.value = 1
        dut.stall.value = 1
        await ClockCycles(dut.clk, 1)  # Wait for stall to take effect
        assert dut.pc.value == expected_pc  # PC should not change during stall
        coverage.operations["branch_stall"] += 1
        
        # Release stall
        dut.stall.value = 0
        await ClockCycles(dut.clk, 1)  # Wait for branch to complete
        assert dut.pc.value == next_target
        coverage.operations["branch"] += 1
        coverage.transitions["increment_to_branch"] += 1

@cocotb.test()
async def test_multiple_stalls(dut):
    """Test multiple stall operations."""
    await initialize_dut(dut)
    
    # Test stall at different points
    test_points = [0x8, 0x10, 0x18, 0x20]
    for point in test_points:
        # Run until we reach the test point
        while dut.pc.value != point:
            await Timer(10, units="ns")
            coverage.operations["increment"] += 1
            coverage.addresses["sequential"] += 1
        
        # Apply stall
        dut.stall.value = 1
        coverage.operations["stall"] += 1
        coverage.transitions["increment_to_stall"] += 1
        
        # Hold stall for a few cycles
        for _ in range(3):
            await Timer(10, units="ns")
            assert dut.pc.value == point, f"PC should maintain value during stall"
        
        # Release stall
        dut.stall.value = 0
        coverage.transitions["stall_to_increment"] += 1
        await Timer(10, units="ns")
        assert dut.pc.value == point + 4, f"PC should increment after stall"
        coverage.operations["increment"] += 1 