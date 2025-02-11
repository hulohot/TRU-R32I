#!/usr/bin/env python3

import subprocess
import os
import sys
import binascii

def compile_assembly(input_file, output_hex):
    """Compile RISC-V assembly to machine code and convert to hex format"""
    # Compile assembly to object file
    obj_file = input_file.replace('.s', '.o')
    subprocess.run(['riscv64-unknown-elf-gcc', '-march=rv32i', '-mabi=ilp32', 
                   '-c', input_file, '-o', obj_file], check=True)
    
    # Extract binary
    bin_file = input_file.replace('.s', '.bin')
    subprocess.run(['riscv64-unknown-elf-objcopy', '-O', 'binary', 
                   obj_file, bin_file], check=True)
    
    # Convert binary to hex format
    with open(bin_file, 'rb') as f:
        binary = f.read()
    
    # Write hex file
    with open(output_hex, 'w') as f:
        for i in range(0, len(binary), 4):
            # Get 4 bytes and reverse for little endian
            word = binary[i:i+4][::-1]
            # Convert to hex and write
            hex_word = binascii.hexlify(word).decode()
            f.write(f"{hex_word}\n")
    
    # Cleanup temporary files
    os.remove(obj_file)
    os.remove(bin_file)

def main():
    if len(sys.argv) != 3:
        print("Usage: compile_test.py <input.s> <output.hex>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_hex = sys.argv[2]
    
    try:
        compile_assembly(input_file, output_hex)
        print(f"Successfully compiled {input_file} to {output_hex}")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling assembly: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 