#!/usr/bin/env python3
import os
import subprocess
import tempfile
from pathlib import Path

class ProgramLoader:
    def __init__(self, build_dir="build"):
        self.build_dir = Path(build_dir)
        self.build_dir.mkdir(exist_ok=True)
        
    def assemble_program(self, source_file):
        """Assemble a RISC-V assembly program into machine code."""
        output_file = self.build_dir / f"{Path(source_file).stem}.o"
        hex_file = self.build_dir / f"{Path(source_file).stem}.hex"
        
        # Assemble the program
        result = subprocess.run([
            "riscv64-unknown-elf-as", "-march=rv32i", "-mabi=ilp32",
            "-o", str(output_file), source_file
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Assembly failed:\n{result.stderr}")
            
        # Convert to hex format
        result = subprocess.run([
            "riscv64-unknown-elf-objcopy", "-O", "verilog",
            str(output_file), str(hex_file)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Hex conversion failed:\n{result.stderr}")
            
        return hex_file
        
    def load_program(self, hex_file):
        """Load a program in hex format into instruction memory."""
        # Read the hex file
        with open(hex_file, 'r') as f:
            program = f.readlines()
            
        # Convert to 32-bit words
        words = []
        for line in program:
            line = line.strip()
            if line and not line.startswith('#'):
                # Skip address markers (@) and empty lines
                if line.startswith('@'):
                    continue
                # Convert hex string to integer
                try:
                    words.append(int(line, 16))
                except ValueError:
                    continue
                
        return words
        
    def assemble_and_load(self, source_file):
        """Assemble and load a RISC-V assembly program."""
        hex_file = self.assemble_program(source_file)
        return self.load_program(hex_file)

def create_test_program(instructions):
    """Create a temporary assembly file with the given instructions."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
        f.write(".section .text\n")
        f.write(".globl _start\n\n")
        f.write("_start:\n")
        for instr in instructions:
            f.write(f"    {instr}\n")
        f.write("    nop\n")
        return f.name

if __name__ == "__main__":
    # Example usage
    loader = ProgramLoader()
    
    # Test with Fibonacci program
    fib_program = loader.assemble_and_load("tb/programs/fibonacci.s")
    print("Fibonacci program loaded:", len(fib_program), "instructions")
    
    # Test with custom instructions
    test_instructions = [
        "addi x1, x0, 10",
        "addi x2, x0, 20",
        "add x3, x1, x2",
        "sw x3, 0(x0)"
    ]
    
    test_file = create_test_program(test_instructions)
    test_program = loader.assemble_and_load(test_file)
    print("Test program loaded:", len(test_program), "instructions")
    os.unlink(test_file)  # Clean up temporary file 