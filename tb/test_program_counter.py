import cocotb
from cocotb.triggers import Timer, ClockCycles
from cocotb.clock import Clock
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
    reset_value = int(dut.pc_current.value)
    assert reset_value == 0x1000, f"PC should be 0x1000 in reset, got 0x{reset_value:08x}"
    
    # Release reset
    dut.rst_n.value = 1
    coverage.transitions["reset_to_increment"] += 1
    await Timer(20, units="ns")
    
    # Check PC increments after reset
    pc_value = int(dut.pc_current.value)
    assert pc_value == 0x1008, f"PC should be 0x1008 after reset, got 0x{pc_value:08x}"
    coverage.operations["increment"] += 1
    coverage.addresses["word_aligned"] += 1

@cocotb.test()
async def test_sequential_increment(dut):
    """Test normal sequential instruction fetching."""
    await initialize_dut(dut)
    await Timer(10, units="ns")
    
    # Check several cycles of sequential increment
    expected_pc = 0x1008  # After initialize_dut, we should be at RESET_ADDR + 8
    for _ in range(5):
        pc_value = int(dut.pc_current.value)
        assert pc_value == expected_pc, f"PC should be 0x{expected_pc:08x}, got 0x{pc_value:08x}"
        coverage.operations["increment"] += 1
        coverage.addresses["sequential"] += 1
        coverage.addresses["word_aligned"] += 1
        await Timer(10, units="ns")
        expected_pc += 4

@cocotb.test()
async def test_stall(dut):
    """Test stall behavior."""
    await initialize_dut(dut)
    
    # Wait for any initialization effects to settle
    await Timer(20, units="ns")
    
    # Get current PC value
    current_pc = int(dut.pc_current.value)
    cocotb.log.info(f"Initial PC value: 0x{current_pc:08x}")
    
    # Assert stall
    dut.stall.value = 1
    coverage.operations["stall"] += 1
    coverage.transitions["increment_to_stall"] += 1
    
    # Check PC value immediately after asserting stall
    await Timer(1, units="ns")
    pc_value = int(dut.pc_current.value)
    cocotb.log.info(f"PC value right after stall: 0x{pc_value:08x}")
    assert pc_value == current_pc, f"PC changed immediately after stall (expected 0x{current_pc:08x}, got 0x{pc_value:08x})"
    
    # Check PC remains stable for several clock cycles
    for i in range(3):
        await Timer(10, units="ns")
        pc_value = int(dut.pc_current.value)
        cocotb.log.info(f"PC value during stall cycle {i}: 0x{pc_value:08x}")
        assert pc_value == current_pc, f"PC changed during stall cycle {i} (expected 0x{current_pc:08x}, got 0x{pc_value:08x})"
    
    # Release stall
    dut.stall.value = 0
    coverage.transitions["stall_to_increment"] += 1
    
    # Wait for next clock edge and check increment
    await Timer(10, units="ns")
    expected_pc = current_pc + 4
    pc_value = int(dut.pc_current.value)
    cocotb.log.info(f"PC value after stall release: 0x{pc_value:08x} (expected 0x{expected_pc:08x})")
    assert pc_value == expected_pc, f"PC did not increment correctly after stall (expected 0x{expected_pc:08x}, got 0x{pc_value:08x})"
    coverage.operations["increment"] += 1

@cocotb.test()
async def test_branch(dut):
    """Test branch behavior."""
    await initialize_dut(dut)
    await Timer(10, units="ns")
    
    # Take a branch
    branch_target = 0x1000
    dut.branch_taken.value = 1
    dut.branch_target.value = branch_target >> 2  # Convert to word address
    coverage.operations["branch"] += 1
    coverage.transitions["increment_to_branch"] += 1
    coverage.addresses["branch_target"] += 1
    
    await Timer(10, units="ns")
    
    # Verify branch was taken
    assert dut.pc_current.value == branch_target, f"PC should be {hex(branch_target)} after branch taken, got {dut.pc_current.value}"
    
    # Return to sequential execution
    dut.branch_taken.value = 0
    coverage.transitions["branch_to_increment"] += 1
    await Timer(10, units="ns")
    
    # Verify normal increment after branch
    assert dut.pc_current.value == branch_target + 4, f"PC should be {hex(branch_target + 4)}, got {dut.pc_current.value}"
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
    
    # Test branch to near-max address (within valid range)
    max_addr = 0x1FF0  # Near maximum valid address (MAX_ADDR - 16)
    dut.branch_target.value = max_addr >> 2  # Convert to word address
    dut.branch_taken.value = 1
    await ClockCycles(dut.clk, 2)  # Wait for branch to take effect
    assert dut.pc_current.value == max_addr, f"PC should be {hex(max_addr)}, got {dut.pc_current.value}"
    coverage.operations["branch"] += 1
    coverage.addresses["near_max"] += 1
    coverage.transitions["increment_to_branch"] += 1
    
    # Test branch with stall
    branch_addr = 0x1000
    dut.branch_target.value = branch_addr >> 2  # Convert to word address
    dut.stall.value = 1
    await ClockCycles(dut.clk, 2)  # Wait for stall to take effect
    assert dut.pc_current.value == max_addr, f"PC should maintain {hex(max_addr)} during stall, got {dut.pc_current.value}"
    coverage.operations["branch_stall"] += 1
    
    # Release stall and complete branch
    dut.stall.value = 0
    await ClockCycles(dut.clk, 2)  # Wait for branch to complete
    assert dut.pc_current.value == branch_addr, f"PC should be {hex(branch_addr)}, got {dut.pc_current.value}"
    coverage.operations["branch"] += 1
    coverage.transitions["branch_to_increment"] += 1

@cocotb.test()
async def test_multiple_branches(dut):
    """Test multiple branch operations."""
    await initialize_dut(dut)
    
    # Test multiple branch targets
    test_targets = [0x1100, 0x1200, 0x1300, 0x1400]
    
    for target in test_targets:
        # Take branch
        dut.branch_taken.value = 1
        dut.branch_target.value = target >> 2  # Convert to word address
        await Timer(20, units="ns")
        
        # Verify branch was taken
        assert dut.pc_current.value == target, f"PC should be {hex(target)}, got {dut.pc_current.value}"
        coverage.operations["branch"] += 1
        coverage.addresses["word_aligned"] += 1
        coverage.transitions["increment_to_branch"] += 1
        
        # Return to sequential execution
        dut.branch_taken.value = 0
        await Timer(10, units="ns")
        
        # Verify normal increment after branch
        expected_pc = target + 4
        assert dut.pc_current.value == expected_pc, f"PC should be {hex(expected_pc)}, got {dut.pc_current.value}"
        coverage.addresses["sequential"] += 1
        coverage.operations["increment"] += 1
        coverage.transitions["branch_to_increment"] += 1

@cocotb.test()
async def test_multiple_stalls(dut):
    """Test multiple stall operations."""
    await initialize_dut(dut)
    
    # Test stall at different points, offset by RESET_ADDR
    test_points = [0x1008, 0x1010, 0x1018, 0x1020]  # Starting from RESET_ADDR + 8
    for point in test_points:
        # Run until we reach the test point
        current_pc = int(dut.pc_current.value)
        while current_pc != point:
            await Timer(10, units="ns")
            current_pc = int(dut.pc_current.value)
            coverage.operations["increment"] += 1
            coverage.addresses["sequential"] += 1
        
        # Apply stall
        dut.stall.value = 1
        coverage.operations["stall"] += 1
        coverage.transitions["increment_to_stall"] += 1
        
        # Hold stall for a few cycles
        for _ in range(3):
            await Timer(10, units="ns")
            current_pc = int(dut.pc_current.value)
            assert current_pc == point, f"PC should maintain value 0x{point:08x} during stall, got 0x{current_pc:08x}"
        
        # Release stall
        dut.stall.value = 0
        coverage.transitions["stall_to_increment"] += 1
        await Timer(10, units="ns")
        current_pc = int(dut.pc_current.value)
        assert current_pc == point + 4, f"PC should be 0x{(point + 4):08x} after stall, got 0x{current_pc:08x}"
        coverage.operations["increment"] += 1 