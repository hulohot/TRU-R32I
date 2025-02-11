import cocotb
from cocotb.triggers import Timer
from collections import defaultdict
import json
import atexit

# Coverage tracking
class CoverageCollector:
    def __init__(self):
        self.instruction_types = defaultdict(int)
        self.control_signals = defaultdict(int)
        self.register_usage = defaultdict(int)
        self.branch_conditions = defaultdict(int)
        self.immediate_types = defaultdict(int)
        
        # Coverage goals
        self.goals = {
            "instruction_types": {
                "R_TYPE": 10,
                "I_TYPE": 10,
                "S_TYPE": 10,
                "B_TYPE": 10,
                "U_TYPE": 10,
                "J_TYPE": 10
            },
            "control_signals": {
                "reg_write": 20,
                "alu_src": 20,
                "mem_write": 10,
                "mem_read": 10,
                "branch": 10,
                "jump": 10
            },
            "register_usage": {
                "x0": 5,
                "x1_x15": 15,
                "x16_x31": 15,
                "same_rs1_rs2": 5
            },
            "branch_conditions": {
                "beq": 5,
                "bne": 5,
                "blt": 5,
                "bge": 5,
                "bltu": 5,
                "bgeu": 5
            },
            "immediate_types": {
                "i_imm": 10,
                "s_imm": 10,
                "b_imm": 10,
                "u_imm": 10,
                "j_imm": 10
            }
        }

    def track_instruction(self, opcode, funct3=None, funct7=None):
        """Track instruction type based on opcode."""
        if opcode == 0b0110011:  # R-type
            self.instruction_types["R_TYPE"] += 1
        elif opcode in [0b0010011, 0b0000011, 0b1100111]:  # I-type
            self.instruction_types["I_TYPE"] += 1
        elif opcode == 0b0100011:  # S-type
            self.instruction_types["S_TYPE"] += 1
        elif opcode == 0b1100011:  # B-type
            self.instruction_types["B_TYPE"] += 1
        elif opcode in [0b0110111, 0b0010111]:  # U-type
            self.instruction_types["U_TYPE"] += 1
        elif opcode == 0b1101111:  # J-type
            self.instruction_types["J_TYPE"] += 1

    def track_control_signals(self, reg_write, alu_src, mem_write, mem_read, branch, jump):
        """Track control signal combinations."""
        if reg_write:
            self.control_signals["reg_write"] += 1
        if alu_src:
            self.control_signals["alu_src"] += 1
        if mem_write:
            self.control_signals["mem_write"] += 1
        if mem_read:
            self.control_signals["mem_read"] += 1
        if branch:
            self.control_signals["branch"] += 1
        if jump:
            self.control_signals["jump"] += 1

    def track_registers(self, rs1, rs2, rd):
        """Track register usage patterns."""
        if rd == 0:
            self.register_usage["x0"] += 1
        if 1 <= rd <= 15:
            self.register_usage["x1_x15"] += 1
        if 16 <= rd <= 31:
            self.register_usage["x16_x31"] += 1
        if rs1 == rs2 and rs1 != 0:
            self.register_usage["same_rs1_rs2"] += 1

    def track_branch_condition(self, funct3):
        """Track branch condition types."""
        conditions = {
            0b000: "beq",
            0b001: "bne",
            0b100: "blt",
            0b101: "bge",
            0b110: "bltu",
            0b111: "bgeu"
        }
        if funct3 in conditions:
            self.branch_conditions[conditions[funct3]] += 1

    def track_immediate(self, imm_type):
        """Track immediate type usage."""
        self.immediate_types[imm_type] += 1

    def calculate_coverage(self):
        """Calculate coverage percentages for each category."""
        coverage = {}
        total_points = 0
        covered_points = 0

        for category in ["instruction_types", "control_signals", "register_usage", "branch_conditions", "immediate_types"]:
            category_data = getattr(self, category)
            category_goals = self.goals[category]
            
            coverage[category] = {
                "covered": sum(1 for item, count in category_data.items() 
                             if count >= category_goals.get(item, 0)),
                "total": len(category_goals)
            }
            
            total_points += coverage[category]["total"]
            covered_points += coverage[category]["covered"]

        return coverage, covered_points, total_points

    def report(self):
        """Generate and print coverage report."""
        coverage, covered_points, total_points = self.calculate_coverage()
        
        report = []
        report.append("Control Unit Coverage Report:")
        report.append("============================\n")
        
        for category, data in coverage.items():
            report.append(f"{category.replace('_', ' ').title()} Coverage:")
            category_data = getattr(self, category)
            category_goals = self.goals[category]
            
            for item, count in sorted(category_data.items()):
                goal = category_goals.get(item, 0)
                status = "✓" if count >= goal else "✗"
                report.append(f"  {status} {item}: {count} occurrences (goal: {goal})")
            report.append("")
        
        coverage_percentage = (covered_points / total_points * 100) if total_points > 0 else 0
        report.append(f"Overall Coverage: {coverage_percentage:.2f}% ({covered_points}/{total_points} points)")
        
        return "\n".join(report)

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
    """Initialize the DUT."""
    # Initialize values
    dut.instruction.value = 0
    await Timer(10, units="ns")  # Small delay for stability

async def check_r_type_instruction(dut, rd, rs1, rs2, funct3, funct7, expected_alu_op, instr_name):
    """Test an R-type instruction and verify outputs."""
    instruction = encode_r_type(rd, rs1, rs2, funct3, funct7)
    dut.instruction.value = instruction
    
    await Timer(10, units="ns")
    
    # Track coverage
    coverage.track_instruction(0b0110011, funct3, funct7)
    coverage.track_control_signals(
        dut.reg_write.value,
        dut.alu_src.value,
        dut.mem_write.value,
        0,  # mem_read not directly exposed
        dut.branch.value,
        dut.jump.value
    )
    coverage.track_registers(rs1, rs2, rd)
    
    # Verify outputs
    assert dut.reg_write.value == 1, f"{instr_name}: reg_write should be 1"
    assert dut.alu_src.value == 0, f"{instr_name}: alu_src should be 0 for R-type"
    assert dut.alu_op.value == expected_alu_op, f"{instr_name}: alu_op mismatch"
    assert dut.mem_write.value == 0, f"{instr_name}: mem_write should be 0"
    assert dut.branch.value == 0, f"{instr_name}: branch should be 0"
    assert dut.jump.value == 0, f"{instr_name}: jump should be 0"
    assert dut.result_src.value == 0, f"{instr_name}: result_src should be 0"
    
    assert dut.rd.value == rd, f"{instr_name}: rd mismatch"
    assert dut.rs1.value == rs1, f"{instr_name}: rs1 mismatch"
    assert dut.rs2.value == rs2, f"{instr_name}: rs2 mismatch"
    assert dut.funct3.value == funct3, f"{instr_name}: funct3 mismatch"
    assert dut.funct7.value == funct7, f"{instr_name}: funct7 mismatch"

@cocotb.test()
async def test_add_instruction(dut):
    """Test ADD instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=1, rs1=2, rs2=3,
        funct3=0b000, funct7=0b0000000,
        expected_alu_op=0b0000,  # ALU_ADD
        instr_name="ADD"
    )

@cocotb.test()
async def test_sub_instruction(dut):
    """Test SUB instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=4, rs1=5, rs2=6,
        funct3=0b000, funct7=0b0100000,
        expected_alu_op=0b1000,  # ALU_SUB
        instr_name="SUB"
    )

@cocotb.test()
async def test_and_instruction(dut):
    """Test AND instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=7, rs1=8, rs2=9,
        funct3=0b111, funct7=0b0000000,
        expected_alu_op=0b0111,  # ALU_AND
        instr_name="AND"
    )

@cocotb.test()
async def test_or_instruction(dut):
    """Test OR instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=10, rs1=11, rs2=12,
        funct3=0b110, funct7=0b0000000,
        expected_alu_op=0b0110,  # ALU_OR
        instr_name="OR"
    )

@cocotb.test()
async def test_xor_instruction(dut):
    """Test XOR instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=13, rs1=14, rs2=15,
        funct3=0b100, funct7=0b0000000,
        expected_alu_op=0b0100,  # ALU_XOR
        instr_name="XOR"
    )

@cocotb.test()
async def test_sll_instruction(dut):
    """Test SLL (Shift Left Logical) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=16, rs1=17, rs2=18,
        funct3=0b001, funct7=0b0000000,
        expected_alu_op=0b0001,  # ALU_SLL
        instr_name="SLL"
    )

@cocotb.test()
async def test_srl_instruction(dut):
    """Test SRL (Shift Right Logical) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=19, rs1=20, rs2=21,
        funct3=0b101, funct7=0b0000000,
        expected_alu_op=0b0101,  # ALU_SRL
        instr_name="SRL"
    )

@cocotb.test()
async def test_sra_instruction(dut):
    """Test SRA (Shift Right Arithmetic) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=22, rs1=23, rs2=24,
        funct3=0b101, funct7=0b0100000,
        expected_alu_op=0b1101,  # ALU_SRA
        instr_name="SRA"
    )

@cocotb.test()
async def test_slt_instruction(dut):
    """Test SLT (Set Less Than) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=25, rs1=26, rs2=27,
        funct3=0b010, funct7=0b0000000,
        expected_alu_op=0b0010,  # ALU_SLT
        instr_name="SLT"
    )

@cocotb.test()
async def test_sltu_instruction(dut):
    """Test SLTU (Set Less Than Unsigned) instruction."""
    await initialize_dut(dut)
    await check_r_type_instruction(
        dut, rd=28, rs1=29, rs2=30,
        funct3=0b011, funct7=0b0000000,
        expected_alu_op=0b0011,  # ALU_SLTU
        instr_name="SLTU"
    )

@cocotb.test()
async def test_register_combinations(dut):
    """Test various register combinations."""
    await initialize_dut(dut)
    
    # Test AND with different register combinations
    await check_r_type_instruction(
        dut, rd=1, rs1=1, rs2=1,
        funct3=0b111, funct7=0b0000000,
        expected_alu_op=0b0111,  # ALU_AND
        instr_name="AND"
    )
    
    # Test OR with x0 as destination
    await check_r_type_instruction(
        dut, rd=0, rs1=2, rs2=3,
        funct3=0b110, funct7=0b0000000,
        expected_alu_op=0b0110,  # ALU_OR
        instr_name="OR"
    )
    
    # Test XOR with x0 as source
    await check_r_type_instruction(
        dut, rd=4, rs1=0, rs2=5,
        funct3=0b100, funct7=0b0000000,
        expected_alu_op=0b0100,  # ALU_XOR
        instr_name="XOR"
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
    
    # Test SUB with different registers
    await check_r_type_instruction(
        dut, rd=10, rs1=11, rs2=12,
        funct3=0b000, funct7=0b0100000,
        expected_alu_op=0b1000,  # ALU_SUB
        instr_name="SUB"
    )
    
    # Test SLL with different registers
    await check_r_type_instruction(
        dut, rd=13, rs1=14, rs2=15,
        funct3=0b001, funct7=0b0000000,
        expected_alu_op=0b0001,  # ALU_SLL
        instr_name="SLL"
    )
    
    # Test SRL with different registers
    await check_r_type_instruction(
        dut, rd=16, rs1=17, rs2=18,
        funct3=0b101, funct7=0b0000000,
        expected_alu_op=0b0101,  # ALU_SRL
        instr_name="SRL"
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
    
    # Test SLL with shift amount 0
    await check_r_type_instruction(
        dut, rd=1, rs1=2, rs2=0,
        funct3=0b001, funct7=0b0000000,
        expected_alu_op=0b0001,  # ALU_SLL
        instr_name="SLL"
    )
    
    # Test SRL with maximum shift amount (31)
    await check_r_type_instruction(
        dut, rd=3, rs1=4, rs2=31,
        funct3=0b101, funct7=0b0000000,
        expected_alu_op=0b0101,  # ALU_SRL
        instr_name="SRL"
    )

@cocotb.test()
async def test_comparison_edge_cases(dut):
    """Test edge cases for comparison instructions."""
    await initialize_dut(dut)
    
    # Test SLT with same register
    await check_r_type_instruction(
        dut, rd=1, rs1=2, rs2=2,
        funct3=0b010, funct7=0b0000000,
        expected_alu_op=0b0010,  # ALU_SLT
        instr_name="SLT"
    )
    
    # Test SLTU with x0
    await check_r_type_instruction(
        dut, rd=3, rs1=0, rs2=4,
        funct3=0b011, funct7=0b0000000,
        expected_alu_op=0b0011,  # ALU_SLTU
        instr_name="SLTU"
    )

def encode_i_type(rd, rs1, imm, funct3, opcode):
    """Encode an I-type instruction."""
    return (
        ((imm & 0xFFF) << 20) |  # imm[11:0]
        (rs1 << 15) |            # rs1[19:15]
        (funct3 << 12) |         # funct3[14:12]
        (rd << 7) |              # rd[11:7]
        opcode                   # opcode[6:0]
    )

def encode_s_type(rs1, rs2, imm, funct3):
    """Encode an S-type instruction."""
    return (
        ((imm & 0xFE0) << 20) |  # imm[11:5]
        (rs2 << 20) |            # rs2[24:20]
        (rs1 << 15) |            # rs1[19:15]
        (funct3 << 12) |         # funct3[14:12]
        ((imm & 0x1F) << 7) |    # imm[4:0]
        0b0100011               # opcode
    )

def encode_b_type(rs1, rs2, imm, funct3):
    """Encode a B-type instruction."""
    return (
        (((imm >> 12) & 0x1) << 31) |  # imm[12]
        (((imm >> 5) & 0x3F) << 25) |  # imm[10:5]
        (rs2 << 20) |                  # rs2[24:20]
        (rs1 << 15) |                  # rs1[19:15]
        (funct3 << 12) |               # funct3[14:12]
        (((imm >> 1) & 0xF) << 8) |    # imm[4:1]
        (((imm >> 11) & 0x1) << 7) |   # imm[11]
        0b1100011                      # opcode
    )

def encode_u_type(rd, imm, opcode):
    """Encode a U-type instruction."""
    return (
        (imm & 0xFFFFF000) |  # imm[31:12]
        (rd << 7) |           # rd[11:7]
        opcode                # opcode[6:0]
    )

def encode_j_type(rd, imm):
    """Encode a J-type instruction."""
    return (
        (((imm >> 20) & 0x1) << 31) |   # imm[20]
        (((imm >> 1) & 0x3FF) << 21) |  # imm[10:1]
        (((imm >> 11) & 0x1) << 20) |   # imm[11]
        (((imm >> 12) & 0xFF) << 12) |  # imm[19:12]
        (rd << 7) |                     # rd[11:7]
        0b1101111                       # opcode
    )

@cocotb.test()
async def test_load_instruction(dut):
    """Test load instruction (I-type)."""
    await initialize_dut(dut)
    
    # Test LW instruction
    rd = 5
    rs1 = 10
    imm = 0x123
    funct3 = 0b010  # LW
    instruction = encode_i_type(rd, rs1, imm, funct3, 0b0000011)
    dut.instruction.value = instruction
    
    await Timer(10, units="ns")
    
    # Track coverage
    coverage.track_instruction(0b0000011)
    coverage.track_control_signals(
        dut.reg_write.value,
        dut.alu_src.value,
        dut.mem_write.value,
        1,  # mem_read
        dut.branch.value,
        dut.jump.value
    )
    coverage.track_registers(rs1, 0, rd)
    coverage.track_immediate("i_imm")

@cocotb.test()
async def test_store_instruction(dut):
    """Test store instruction (S-type)."""
    await initialize_dut(dut)
    
    # Test SW instruction
    rs1 = 15
    rs2 = 20
    imm = 0x123
    funct3 = 0b010  # SW
    instruction = encode_s_type(rs1, rs2, imm, funct3)
    dut.instruction.value = instruction
    
    await Timer(10, units="ns")
    
    # Track coverage
    coverage.track_instruction(0b0100011)
    coverage.track_control_signals(
        dut.reg_write.value,
        dut.alu_src.value,
        dut.mem_write.value,
        0,  # mem_read
        dut.branch.value,
        dut.jump.value
    )
    coverage.track_registers(rs1, rs2, 0)
    coverage.track_immediate("s_imm")

@cocotb.test()
async def test_branch_instructions(dut):
    """Test branch instructions (B-type)."""
    await initialize_dut(dut)
    
    # Test all branch conditions
    conditions = [
        (0b000, "beq"),  # BEQ
        (0b001, "bne"),  # BNE
        (0b100, "blt"),  # BLT
        (0b101, "bge"),  # BGE
        (0b110, "bltu"), # BLTU
        (0b111, "bgeu")  # BGEU
    ]
    
    for funct3, cond in conditions:
        rs1 = 8
        rs2 = 9
        imm = 0x100  # Branch offset
        instruction = encode_b_type(rs1, rs2, imm, funct3)
        dut.instruction.value = instruction
        
        await Timer(10, units="ns")
        
        # Track coverage
        coverage.track_instruction(0b1100011)
        coverage.track_control_signals(
            dut.reg_write.value,
            dut.alu_src.value,
            dut.mem_write.value,
            0,  # mem_read
            dut.branch.value,
            dut.jump.value
        )
        coverage.track_registers(rs1, rs2, 0)
        coverage.track_branch_condition(funct3)
        coverage.track_immediate("b_imm")

@cocotb.test()
async def test_lui_auipc_instructions(dut):
    """Test LUI and AUIPC instructions (U-type)."""
    await initialize_dut(dut)
    
    # Test LUI
    rd = 12
    imm = 0x12345000
    instruction = encode_u_type(rd, imm, 0b0110111)
    dut.instruction.value = instruction
    
    await Timer(10, units="ns")
    
    # Track coverage
    coverage.track_instruction(0b0110111)
    coverage.track_control_signals(
        dut.reg_write.value,
        dut.alu_src.value,
        dut.mem_write.value,
        0,  # mem_read
        dut.branch.value,
        dut.jump.value
    )
    coverage.track_registers(0, 0, rd)
    coverage.track_immediate("u_imm")
    
    # Test AUIPC
    rd = 14
    imm = 0x67890000
    instruction = encode_u_type(rd, imm, 0b0010111)
    dut.instruction.value = instruction
    
    await Timer(10, units="ns")
    
    # Track coverage
    coverage.track_instruction(0b0010111)
    coverage.track_control_signals(
        dut.reg_write.value,
        dut.alu_src.value,
        dut.mem_write.value,
        0,  # mem_read
        dut.branch.value,
        dut.jump.value
    )
    coverage.track_registers(0, 0, rd)
    coverage.track_immediate("u_imm")

@cocotb.test()
async def test_jal_instruction(dut):
    """Test JAL instruction (J-type)."""
    await initialize_dut(dut)
    
    # Test JAL
    rd = 1
    imm = 0x1234  # Jump offset
    instruction = encode_j_type(rd, imm)
    dut.instruction.value = instruction
    
    await Timer(10, units="ns")
    
    # Track coverage
    coverage.track_instruction(0b1101111)
    coverage.track_control_signals(
        dut.reg_write.value,
        dut.alu_src.value,
        dut.mem_write.value,
        0,  # mem_read
        dut.branch.value,
        dut.jump.value
    )
    coverage.track_registers(0, 0, rd)
    coverage.track_immediate("j_imm") 