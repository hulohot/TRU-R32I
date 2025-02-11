import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from collections import defaultdict
import json
import atexit

# Coverage tracking
class CoverageCollector:
    def __init__(self):
        self.instruction_types = defaultdict(int)  # Track instruction types tested
        self.control_signals = defaultdict(int)    # Track control signal combinations
        self.register_usage = defaultdict(int)     # Track register combinations used
        
        # Coverage goals
        self.goals = {
            "instruction_types": {
                "ADD": 5,    # Basic arithmetic
                "SUB": 5,    # Subtraction
                "AND": 5,    # Logical AND
                "OR": 5,     # Logical OR
                "XOR": 5,    # Logical XOR
                "SLL": 5,    # Shift left logical
                "SRL": 5,    # Shift right logical
                "SRA": 5,    # Shift right arithmetic
                "SLT": 5,    # Set less than
                "SLTU": 5    # Set less than unsigned
            },
            "control_signals": {
                "reg_write": 10,      # Register write enable
                "alu_src_a": 5,       # ALU source A selection
                "alu_src_b": 5,       # ALU source B selection
                "alu_op_add": 5,      # ALU operation - ADD
                "alu_op_sub": 5,      # ALU operation - SUB
                "alu_op_and": 5,      # ALU operation - AND
                "alu_op_or": 5,       # ALU operation - OR
                "alu_op_xor": 5,      # ALU operation - XOR
                "alu_op_sll": 5,      # ALU operation - SLL
                "alu_op_srl": 5,      # ALU operation - SRL
                "alu_op_sra": 5,      # ALU operation - SRA
                "alu_op_slt": 5,      # ALU operation - SLT
                "alu_op_sltu": 5      # ALU operation - SLTU
            },
            "register_usage": {
                "x0": 5,              # Zero register
                "x1_x15": 10,         # Lower registers
                "x16_x31": 10,        # Upper registers
                "same_rs1_rs2": 5,    # Same source registers
                "rd_equals_rs1": 5,   # Destination equals first source
                "rd_equals_rs2": 5    # Destination equals second source
            }
        }

    def report(self):
        """Generate and print coverage report"""
        cocotb.log.info("Control Unit Coverage Report:")
        cocotb.log.info("============================")
        
        total_points = 0
        covered_points = 0
        
        # Instruction types coverage
        cocotb.log.info("\nInstruction Types Coverage:")
        for instr, count in sorted(self.instruction_types.items()):
            total_points += 1
            if count >= self.goals["instruction_types"].get(instr, 0):
                covered_points += 1
            cocotb.log.info(f"  {instr}: {count} occurrences (goal: {self.goals['instruction_types'].get(instr, 0)})")
        
        # Control signals coverage
        cocotb.log.info("\nControl Signals Coverage:")
        for signal, count in sorted(self.control_signals.items()):
            total_points += 1
            if count >= self.goals["control_signals"].get(signal, 0):
                covered_points += 1
            cocotb.log.info(f"  {signal}: {count} occurrences (goal: {self.goals['control_signals'].get(signal, 0)})")
        
        # Register usage coverage
        cocotb.log.info("\nRegister Usage Coverage:")
        for reg, count in sorted(self.register_usage.items()):
            total_points += 1
            if count >= self.goals["register_usage"].get(reg, 0):
                covered_points += 1
            cocotb.log.info(f"  {reg}: {count} occurrences (goal: {self.goals['register_usage'].get(reg, 0)})")
        
        # Overall coverage
        coverage_percentage = (covered_points / total_points) * 100 if total_points > 0 else 0
        cocotb.log.info(f"\nOverall Coverage: {coverage_percentage:.2f}% ({covered_points}/{total_points} points)")
        
        # Save coverage data to file
        coverage_data = {
            "instruction_types": dict(self.instruction_types),
            "control_signals": dict(self.control_signals),
            "register_usage": dict(self.register_usage),
            "coverage_percentage": coverage_percentage,
            "covered_points": covered_points,
            "total_points": total_points
        }
        
        with open("coverage_control_unit.json", "w") as f:
            json.dump(coverage_data, f, indent=4)

# Global coverage collector
coverage = CoverageCollector()

# Register coverage report to run at exit
@atexit.register
def save_coverage():
    coverage.report()

# R-type instruction encoding helper
def encode_r_type(rd, rs1, rs2, funct3, funct7):
    return (
        (funct7 << 25) |  # funct7[31:25]
        (rs2 << 20) |    # rs2[24:20]
        (rs1 << 15) |    # rs1[19:15]
        (funct3 << 12) |  # funct3[14:12]
        (rd << 7) |      # rd[11:7]
        0b0110011        # opcode[6:0] for R-type
    )

async def initialize_dut(dut):
    """Initialize the DUT and start the clock."""
    # Create a 10ns period clock
    clock = Clock(dut.clk, 10, units="ns")
    # Start the clock
    cocotb.start_soon(clock.start())
    
    # Initialize values
    dut.rst_n.value = 0
    dut.instruction.value = 0
    
    # Wait 20ns, then release reset
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await Timer(10, units="ns")

async def check_r_type_instruction(dut, rd, rs1, rs2, funct3, funct7, expected_alu_op, instr_name):
    """Test an R-type instruction and verify outputs."""
    # Encode and set the instruction
    instruction = encode_r_type(rd, rs1, rs2, funct3, funct7)
    dut.instruction.value = instruction
    
    # Record coverage
    coverage.instruction_types[instr_name] += 1
    coverage.control_signals["reg_write"] += 1
    coverage.control_signals[f"alu_op_{instr_name.lower()}"] += 1
    
    # Register usage coverage
    if rd == 0 or rs1 == 0 or rs2 == 0:
        coverage.register_usage["x0"] += 1
    if 1 <= rd <= 15 or 1 <= rs1 <= 15 or 1 <= rs2 <= 15:
        coverage.register_usage["x1_x15"] += 1
    if 16 <= rd <= 31 or 16 <= rs1 <= 31 or 16 <= rs2 <= 31:
        coverage.register_usage["x16_x31"] += 1
    if rs1 == rs2:
        coverage.register_usage["same_rs1_rs2"] += 1
    if rd == rs1:
        coverage.register_usage["rd_equals_rs1"] += 1
    if rd == rs2:
        coverage.register_usage["rd_equals_rs2"] += 1
    
    # Wait for 2 clock cycles
    await Timer(20, units="ns")
    
    # Check all outputs
    assert dut.rd.value == rd, f"{instr_name}: rd mismatch, got {dut.rd.value} expected {rd}"
    assert dut.rs1.value == rs1, f"{instr_name}: rs1 mismatch, got {dut.rs1.value} expected {rs1}"
    assert dut.rs2.value == rs2, f"{instr_name}: rs2 mismatch, got {dut.rs2.value} expected {rs2}"
    assert dut.opcode.value == 0b0110011, f"{instr_name}: opcode mismatch"
    assert dut.funct3.value == funct3, f"{instr_name}: funct3 mismatch"
    assert dut.funct7.value == funct7, f"{instr_name}: funct7 mismatch"
    assert dut.reg_write_en.value == 1, f"{instr_name}: reg_write_en should be 1"
    assert dut.alu_op.value == expected_alu_op, f"{instr_name}: alu_op mismatch, got {dut.alu_op.value} expected {expected_alu_op}"
    assert dut.alu_src_a_sel.value == 0, f"{instr_name}: alu_src_a_sel should be 0"
    assert dut.alu_src_b_sel.value == 0, f"{instr_name}: alu_src_b_sel should be 0"

@cocotb.test()
async def test_add_instruction(dut):
    """Test ADD instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=1, rs1=2, rs2=3,
        funct3=0b000, funct7=0b0000000,
        expected_alu_op=0b0000,
        instr_name="ADD"
    )

@cocotb.test()
async def test_sub_instruction(dut):
    """Test SUB instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=4, rs1=5, rs2=6,
        funct3=0b000, funct7=0b0100000,
        expected_alu_op=0b0001,
        instr_name="SUB"
    )

@cocotb.test()
async def test_and_instruction(dut):
    """Test AND instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=7, rs1=8, rs2=9,
        funct3=0b111, funct7=0b0000000,
        expected_alu_op=0b1001,
        instr_name="AND"
    )

@cocotb.test()
async def test_or_instruction(dut):
    """Test OR instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=10, rs1=11, rs2=12,
        funct3=0b110, funct7=0b0000000,
        expected_alu_op=0b1000,
        instr_name="OR"
    )

@cocotb.test()
async def test_xor_instruction(dut):
    """Test XOR instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=13, rs1=14, rs2=15,
        funct3=0b100, funct7=0b0000000,
        expected_alu_op=0b0101,
        instr_name="XOR"
    )

@cocotb.test()
async def test_sll_instruction(dut):
    """Test SLL (Shift Left Logical) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=16, rs1=17, rs2=18,
        funct3=0b001, funct7=0b0000000,
        expected_alu_op=0b0010,
        instr_name="SLL"
    )

@cocotb.test()
async def test_srl_instruction(dut):
    """Test SRL (Shift Right Logical) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=19, rs1=20, rs2=21,
        funct3=0b101, funct7=0b0000000,
        expected_alu_op=0b0110,
        instr_name="SRL"
    )

@cocotb.test()
async def test_sra_instruction(dut):
    """Test SRA (Shift Right Arithmetic) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=22, rs1=23, rs2=24,
        funct3=0b101, funct7=0b0100000,
        expected_alu_op=0b0111,
        instr_name="SRA"
    )

@cocotb.test()
async def test_slt_instruction(dut):
    """Test SLT (Set Less Than) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=25, rs1=26, rs2=27,
        funct3=0b010, funct7=0b0000000,
        expected_alu_op=0b0011,
        instr_name="SLT"
    )

@cocotb.test()
async def test_sltu_instruction(dut):
    """Test SLTU (Set Less Than Unsigned) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=28, rs1=29, rs2=30,
        funct3=0b011, funct7=0b0000000,
        expected_alu_op=0b0100,
        instr_name="SLTU"
    )

@cocotb.test()
async def test_register_combinations(dut):
    """Test various register combinations."""
    await initialize_dut(dut)
    
    # Test using x0 as source and destination
    for _ in range(3):  # Multiple tests with x0
        await check_r_type_instruction(
            dut, rd=0, rs1=0, rs2=0,
            funct3=0b000, funct7=0b0000000,
            expected_alu_op=0b0000,
            instr_name="ADD"
        )
    
    # Test same source registers with different operations
    for op, funct3, funct7, alu_op in [
        ("ADD", 0b000, 0b0000000, 0b0000),
        ("AND", 0b111, 0b0000000, 0b1001),
        ("OR",  0b110, 0b0000000, 0b1000),
        ("XOR", 0b100, 0b0000000, 0b0101)
    ]:
        await check_r_type_instruction(
            dut, rd=15, rs1=10, rs2=10,
            funct3=funct3, funct7=funct7,
            expected_alu_op=alu_op,
            instr_name=op
        )
    
    # Test destination equal to source with different registers
    for rd in [5, 10, 15, 20, 25]:
        await check_r_type_instruction(
            dut, rd=rd, rs1=rd, rs2=rd+1,
            funct3=0b000, funct7=0b0000000,
            expected_alu_op=0b0000,
            instr_name="ADD"
        )

@cocotb.test()
async def test_register_ranges(dut):
    """Test different register ranges."""
    await initialize_dut(dut)
    
    # Test lower registers (x1-x15)
    for rd, rs1, rs2 in [(1,2,3), (4,5,6), (7,8,9), (10,11,12), (13,14,15)]:
        await check_r_type_instruction(
            dut, rd=rd, rs1=rs1, rs2=rs2,
            funct3=0b000, funct7=0b0000000,
            expected_alu_op=0b0000,
            instr_name="ADD"
        )
    
    # Test upper registers (x16-x31)
    for rd, rs1, rs2 in [(16,17,18), (19,20,21), (22,23,24), (25,26,27), (28,29,30)]:
        await check_r_type_instruction(
            dut, rd=rd, rs1=rs1, rs2=rs2,
            funct3=0b000, funct7=0b0000000,
            expected_alu_op=0b0000,
            instr_name="ADD"
        )

@cocotb.test()
async def test_all_operations_multiple(dut):
    """Test all operations multiple times with different registers."""
    await initialize_dut(dut)
    
    operations = [
        ("ADD",  0b000, 0b0000000, 0b0000),
        ("SUB",  0b000, 0b0100000, 0b0001),
        ("AND",  0b111, 0b0000000, 0b1001),
        ("OR",   0b110, 0b0000000, 0b1000),
        ("XOR",  0b100, 0b0000000, 0b0101),
        ("SLL",  0b001, 0b0000000, 0b0010),
        ("SRL",  0b101, 0b0000000, 0b0110),
        ("SRA",  0b101, 0b0100000, 0b0111),
        ("SLT",  0b010, 0b0000000, 0b0011),
        ("SLTU", 0b011, 0b0000000, 0b0100)
    ]
    
    # Test each operation with different register combinations
    for op, funct3, funct7, alu_op in operations:
        # Test with lower registers
        await check_r_type_instruction(
            dut, rd=1, rs1=2, rs2=3,
            funct3=funct3, funct7=funct7,
            expected_alu_op=alu_op,
            instr_name=op
        )
        
        # Test with upper registers
        await check_r_type_instruction(
            dut, rd=20, rs1=21, rs2=22,
            funct3=funct3, funct7=funct7,
            expected_alu_op=alu_op,
            instr_name=op
        )
        
        # Test with x0 as one of the sources
        await check_r_type_instruction(
            dut, rd=5, rs1=0, rs2=6,
            funct3=funct3, funct7=funct7,
            expected_alu_op=alu_op,
            instr_name=op
        )
        
        # Test with same source registers
        await check_r_type_instruction(
            dut, rd=10, rs1=15, rs2=15,
            funct3=funct3, funct7=funct7,
            expected_alu_op=alu_op,
            instr_name=op
        )
        
        # Test with destination equal to source
        await check_r_type_instruction(
            dut, rd=25, rs1=25, rs2=26,
            funct3=funct3, funct7=funct7,
            expected_alu_op=alu_op,
            instr_name=op
        ) 

@cocotb.test()
async def test_edge_cases(dut):
    """Test edge cases for control unit."""
    await initialize_dut(dut)
    
    # Test using x0 as destination (should still set control signals but write will be ignored)
    await check_r_type_instruction(
        dut, rd=0, rs1=1, rs2=2,
        funct3=0b000, funct7=0b0000000,
        expected_alu_op=0b0000,
        instr_name="ADD"
    )
    
    # Test using x0 as both source registers
    await check_r_type_instruction(
        dut, rd=3, rs1=0, rs2=0,
        funct3=0b000, funct7=0b0000000,
        expected_alu_op=0b0000,
        instr_name="ADD"
    )
    
    # Test using same register for all fields
    await check_r_type_instruction(
        dut, rd=5, rs1=5, rs2=5,
        funct3=0b000, funct7=0b0000000,
        expected_alu_op=0b0000,
        instr_name="ADD"
    )

@cocotb.test()
async def test_boundary_registers(dut):
    """Test boundary cases for register selection."""
    await initialize_dut(dut)
    
    # Test highest register numbers
    await check_r_type_instruction(
        dut, rd=31, rs1=31, rs2=31,
        funct3=0b000, funct7=0b0000000,
        expected_alu_op=0b0000,
        instr_name="ADD"
    )
    
    # Test mix of high and low registers
    await check_r_type_instruction(
        dut, rd=1, rs1=31, rs2=0,
        funct3=0b000, funct7=0b0000000,
        expected_alu_op=0b0000,
        instr_name="ADD"
    )

@cocotb.test()
async def test_all_shift_amounts(dut):
    """Test various shift amounts including edge cases."""
    await initialize_dut(dut)
    
    # Test maximum shift amount (31)
    await check_r_type_instruction(
        dut, rd=1, rs1=2, rs2=31,
        funct3=0b001, funct7=0b0000000,
        expected_alu_op=0b0010,
        instr_name="SLL"
    )
    
    # Test zero shift amount
    await check_r_type_instruction(
        dut, rd=3, rs1=4, rs2=0,
        funct3=0b001, funct7=0b0000000,
        expected_alu_op=0b0010,
        instr_name="SLL"
    )
    
    # Test arithmetic right shift with maximum shift
    await check_r_type_instruction(
        dut, rd=5, rs1=6, rs2=31,
        funct3=0b101, funct7=0b0100000,
        expected_alu_op=0b0100,
        instr_name="SRA"
    )

@cocotb.test()
async def test_comparison_edge_cases(dut):
    """Test edge cases for comparison instructions."""
    await initialize_dut(dut)
    
    # Test SLT with same register (should always be false)
    await check_r_type_instruction(
        dut, rd=1, rs1=2, rs2=2,
        funct3=0b010, funct7=0b0000000,
        expected_alu_op=0b0110,
        instr_name="SLT"
    )
    
    # Test SLTU with x0 (special case since x0 is always 0)
    await check_r_type_instruction(
        dut, rd=3, rs1=0, rs2=1,
        funct3=0b011, funct7=0b0000000,
        expected_alu_op=0b0111,
        instr_name="SLTU"
    ) 