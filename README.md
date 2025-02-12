# A Simple RISCV-32i CPU

This repo is a simple implementation of a RISCV-32i CPU.
I am building this CPU for fun and to understand the RISC-V i instruction set.
In the future I would like to convert it to be asynchonous and use the MTNCL framework.

## Project Overview

This project implements a basic RISC-V CPU supporting the RV32I base integer instruction set. The implementation focuses on clarity and educational value, making it a good reference for understanding RISC-V architecture and CPU design principles.

### Features

- RV32I base integer instruction set implementation
- 5-stage pipeline architecture (Fetch, Decode, Execute, Memory, Writeback)
- Harvard architecture with separate instruction and data memory
- Written in SystemVerilog for hardware synthesis
- Testbench suite for verification

## Architecture

### Core Components

1. **Program Counter (PC)**
   - 32-bit counter
   - Branch and jump handling
   - Reset functionality

2. **Instruction Memory**
   - ROM implementation
   - 32-bit instruction width
   - Word-aligned access

3. **Register File**
   - 32 general-purpose registers (x0-x31)
   - x0 hardwired to zero
   - Dual read ports, single write port

4. **ALU (Arithmetic Logic Unit)**
   - Integer arithmetic operations
   - Logic operations
   - Comparison operations
   - Shift operations

5. **Control Unit**
   - Instruction decoder
   - Control signal generation
   - Pipeline control

6. **Data Memory**
   - RAM implementation
   - Byte-addressable
   - Support for word, half-word, and byte access

### Pipeline Stages

1. **Fetch (IF)**
   - Fetch instruction from memory
   - Update program counter
   - Handle branch prediction

2. **Decode (ID)**
   - Instruction decoding
   - Register file reading
   - Immediate generation
   - Control signal generation

3. **Execute (EX)**
   - ALU operations
   - Branch condition evaluation
   - Address calculation

4. **Memory (MEM)**
   - Data memory access
   - Load/Store operations

5. **Writeback (WB)**
   - Register file writing
   - Result selection

## Implementation Plan

### Phase 1: Basic CPU Core
- [x] Implement basic register file
- [x] Create ALU with fundamental operations
- [x] Design control unit for R-type instructions
- [x] Set up basic instruction fetch logic
- [x] Implement instruction memory with NOP initialization
- [x] Implement single-cycle execution
- [x] Add data memory interface
- [x] Implement load/store instructions
- [x] Add immediate instruction support
- [x] Implement branch/jump instructions

### Phase 2: Memory and Control
- [x] Add data memory interface
- [x] Implement load/store instructions
- [x] Add immediate instruction support
- [x] Implement branch/jump instructions
- [ ] Basic pipeline hazard detection

### Phase 3: Pipelining
- [x] Convert to 5-stage pipeline
- [x] Implement forwarding unit
- [x] Add pipeline registers
- [x] Handle data hazards
- [ ] Implement branch prediction

### Phase 4: Testing and Verification
- [x] Develop comprehensive testbench
- [x] Create instruction test suite
- [ ] Implement performance counters
- [ ] Add debugging support
- [ ] Verify against RISC-V compliance tests

### Phase 5: Optimization and Extensions
- [ ] Pipeline optimization
- [ ] Convert to asynchronous design using MTNCL
- [ ] Add custom extensions
- [ ] Performance analysis and improvements

## Directory Structure

```
.
├── rtl/                    # RTL design files
│   ├── core/              # CPU core components
│   ├── memory/            # Memory modules
│   └── pipeline/          # Pipeline stages
├── tb/                    # Testbench files
├── tests/                 # Test programs
├── docs/                  # Documentation
└── tools/                 # Build and simulation tools
```

## Getting Started

### Prerequisites
- SystemVerilog compatible simulator (e.g., Verilator, ModelSim)
- RISC-V toolchain for test program compilation
- Make or similar build system

### Building and Testing
1. Clone the repository
2. Set up the RISC-V toolchain
3. Run the test suite
4. Simulate using provided testbenches

## Future Enhancements

1. **Asynchronous Implementation**
   - Convert to MTNCL framework
   - Implement delay-insensitive circuits
   - Power optimization

2. **Additional Features**
   - Cache implementation
   - Memory management unit
   - Privilege levels
   - Custom instructions

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Bug fixes
- New features
- Documentation improvements
- Test cases

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- [RISC-V Specification](https://riscv.org/specifications/)
- [RISC-V ISA Manual](https://riscv.org/technical/specifications/)
- [MTNCL Design Methodology]()

