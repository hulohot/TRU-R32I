import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import random
from collections import defaultdict
import json
import atexit

# Coverage tracking
class CoverageCollector:
    def __init__(self):
        self.register_reads = defaultdict(int)  # Track reads per register
        self.register_writes = defaultdict(int)  # Track writes per register
        self.concurrent_ops = defaultdict(int)   # Track concurrent operations
        self.data_patterns = defaultdict(int)    # Track data patterns written
        
        # Coverage goals
        self.goals = {
            "register_reads": {str(i): 1 for i in range(32)},  # Each register should be read at least once
            "register_writes": {str(i): 1 for i in range(1, 32)},  # Each writable register should be written at least once
            "concurrent_ops": {
                "read_after_write": 1,
                "write_after_read": 1,
                "concurrent_read_write": 1
            },
            "data_patterns": {
                "0x00000000": 1,
                "0xFFFFFFFF": 1,
                "0x55555555": 1,
                "0xAAAAAAAA": 1,
                "0x12345678": 1,
                "0xABCDEF01": 1
            }
        }

    def report(self):
        """Generate and print coverage report"""
        cocotb.log.info("Coverage Report:")
        cocotb.log.info("================")
        
        total_points = 0
        covered_points = 0
        
        # Register read coverage
        cocotb.log.info("\nRegister Read Coverage:")
        for reg, count in sorted(self.register_reads.items()):
            total_points += 1
            if count >= self.goals["register_reads"][str(reg)]:
                covered_points += 1
            cocotb.log.info(f"  x{reg}: {count} reads (goal: {self.goals['register_reads'][str(reg)]})")
            
        # Register write coverage
        cocotb.log.info("\nRegister Write Coverage:")
        for reg, count in sorted(self.register_writes.items()):
            if reg != 0:  # x0 is not writable
                total_points += 1
                if count >= self.goals["register_writes"][str(reg)]:
                    covered_points += 1
                cocotb.log.info(f"  x{reg}: {count} writes (goal: {self.goals['register_writes'][str(reg)]})")
            
        # Concurrent operations coverage
        cocotb.log.info("\nConcurrent Operations Coverage:")
        for op, count in sorted(self.concurrent_ops.items()):
            total_points += 1
            if count >= self.goals["concurrent_ops"][op]:
                covered_points += 1
            cocotb.log.info(f"  {op}: {count} occurrences (goal: {self.goals['concurrent_ops'][op]})")
            
        # Data patterns coverage
        cocotb.log.info("\nData Patterns Coverage:")
        for pattern, count in sorted(self.data_patterns.items()):
            pattern_hex = f"0x{pattern:08x}"
            if pattern_hex in self.goals["data_patterns"]:
                total_points += 1
                if count >= self.goals["data_patterns"][pattern_hex]:
                    covered_points += 1
                cocotb.log.info(f"  {pattern_hex}: {count} occurrences (goal: {self.goals['data_patterns'][pattern_hex]})")
        
        # Overall coverage
        coverage_percentage = (covered_points / total_points) * 100 if total_points > 0 else 0
        cocotb.log.info(f"\nOverall Coverage: {coverage_percentage:.2f}% ({covered_points}/{total_points} points)")
        
        # Save coverage data to file
        coverage_data = {
            "register_reads": dict(self.register_reads),
            "register_writes": dict(self.register_writes),
            "concurrent_ops": dict(self.concurrent_ops),
            "data_patterns": {f"0x{pattern:08x}": count for pattern, count in self.data_patterns.items()},
            "coverage_percentage": coverage_percentage,
            "covered_points": covered_points,
            "total_points": total_points
        }
        
        with open("coverage_register_file.json", "w") as f:
            json.dump(coverage_data, f, indent=4)

# Global coverage collector
coverage = CoverageCollector()

# Register coverage report to run at exit
@atexit.register
def save_coverage():
    coverage.report()

async def initialize_dut(dut):
    """Initialize DUT and start clock"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_register_file_reset(dut):
    """Test register file reset behavior"""
    await initialize_dut(dut)
    
    # Check all registers are 0 after reset
    for i in range(32):
        dut.rs1_addr.value = i
        coverage.register_reads[i] += 1
        await Timer(1, units="ns")
        assert int(dut.rs1_data.value) == 0, f"Register {i} not zero after reset"

@cocotb.test()
async def test_x0_read(dut):
    """Test that x0 always reads as 0"""
    await initialize_dut(dut)
    
    # Try to write to x0
    dut.we.value = 1
    dut.rd_addr.value = 0
    coverage.register_writes[0] += 1
    dut.rd_data.value = 0xFFFFFFFF
    coverage.data_patterns[0xFFFFFFFF] += 1
    await RisingEdge(dut.clk)
    
    # Read x0 from both ports
    dut.rs1_addr.value = 0
    dut.rs2_addr.value = 0
    coverage.register_reads[0] += 2  # Both ports
    await Timer(1, units="ns")
    
    assert int(dut.rs1_data.value) == 0, "x0 read from rs1 port is not zero"
    assert int(dut.rs2_data.value) == 0, "x0 read from rs2 port is not zero"

@cocotb.test()
async def test_write_read(dut):
    """Test writing to and reading from registers"""
    await initialize_dut(dut)
    
    # Test data
    test_data = {
        1: 0x12345678,
        2: 0xABCDEF01,
        31: 0xFFFFFFFF
    }
    
    # Write test data
    dut.we.value = 1
    for reg, data in test_data.items():
        dut.rd_addr.value = reg
        coverage.register_writes[reg] += 1
        dut.rd_data.value = data
        coverage.data_patterns[data] += 1
        await RisingEdge(dut.clk)
        coverage.concurrent_ops["write_after_read"] += 1
    
    # Read and verify data
    dut.we.value = 0
    for reg, data in test_data.items():
        # Test both read ports
        dut.rs1_addr.value = reg
        dut.rs2_addr.value = reg
        coverage.register_reads[reg] += 2  # Both ports
        await Timer(1, units="ns")
        coverage.concurrent_ops["read_after_write"] += 1
        
        assert int(dut.rs1_data.value) == data, f"rs1 read wrong value from x{reg}"
        assert int(dut.rs2_data.value) == data, f"rs2 read wrong value from x{reg}"

@cocotb.test()
async def test_concurrent_read_write(dut):
    """Test concurrent read and write operations"""
    await initialize_dut(dut)
    
    # Write initial value
    dut.we.value = 1
    dut.rd_addr.value = 5
    coverage.register_writes[5] += 1
    dut.rd_data.value = 0xAAAAAAAA
    coverage.data_patterns[0xAAAAAAAA] += 1
    await RisingEdge(dut.clk)
    
    # Setup concurrent read of old value and write of new value
    dut.rs1_addr.value = 5
    dut.rs2_addr.value = 5
    coverage.register_reads[5] += 2
    dut.rd_addr.value = 5
    coverage.register_writes[5] += 1
    dut.rd_data.value = 0x55555555
    coverage.data_patterns[0x55555555] += 1
    dut.we.value = 1
    coverage.concurrent_ops["concurrent_read_write"] += 1
    
    # Check old value is read before write
    await Timer(1, units="ns")
    assert int(dut.rs1_data.value) == 0xAAAAAAAA, "Wrong value read during concurrent operation"
    
    # After clock edge, new value should be written
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.rs1_data.value) == 0x55555555, "New value not properly written"

@cocotb.test()
async def test_random_access(dut):
    """Test random access patterns"""
    await initialize_dut(dut)
    
    # Initialize register values after reset
    register_values = {i: 0 for i in range(32)}  # Include x0, all registers should be 0 after reset
    
    # Perform random operations
    for _ in range(100):
        # Randomly choose between read and write
        if random.random() < 0.5:  # Write
            reg = random.randint(1, 31)  # Skip x0
            value = random.randint(0, 0xFFFFFFFF)
            dut.we.value = 1
            dut.rd_addr.value = reg
            dut.rd_data.value = value
            coverage.register_writes[reg] += 1
            coverage.data_patterns[value] += 1
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")  # Wait for write to complete
            register_values[reg] = value  # Update shadow register after write
            coverage.concurrent_ops["write_after_read"] += 1
        else:  # Read
            reg = random.randint(0, 31)  # Include x0 for reads
            dut.we.value = 0
            dut.rs1_addr.value = reg
            coverage.register_reads[reg] += 1
            await Timer(1, units="ns")  # Wait for read to complete
            read_value = int(dut.rs1_data.value)
            expected_value = register_values[reg]
            assert read_value == expected_value, \
                f"Incorrect value read from register {reg}. Expected 0x{expected_value:08x}, got 0x{read_value:08x}"
            coverage.concurrent_ops["read_after_write"] += 1 