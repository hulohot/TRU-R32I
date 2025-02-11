# Makefile for RISC-V CPU project

# Tools
VERILATOR = verilator
PYTHON = python3
RISCV_GCC = riscv64-unknown-elf-gcc
RISCV_OBJCOPY = riscv64-unknown-elf-objcopy
IVERILOG = iverilog

# Coverage settings
COVERAGE_DIR = coverage
export COVERAGE = 1
export COCOTB_ENABLE_COVERAGE = 1
IVERILOG_COV_FLAGS = -g2012 -pfileline=1 -Wall

# Directories
RTL_DIR = rtl
TEST_DIR = tests
TB_DIR = tb
BUILD_DIR = build
TOOLS_DIR = tools

# Source files
RTL_SRCS = $(wildcard $(RTL_DIR)/*.sv) $(wildcard $(RTL_DIR)/core/*.sv) $(wildcard $(RTL_DIR)/memory/*.sv)
TEST_SRCS = $(wildcard $(TEST_DIR)/*.sv)

# Test program
TEST_ASM = $(TEST_DIR)/test_program.s
TEST_ELF = $(BUILD_DIR)/test_program.elf
TEST_BIN = $(BUILD_DIR)/test_program.bin
TEST_HEX = $(BUILD_DIR)/test_program.hex

# Cocotb configuration
export COCOTB_REDUCED_LOG_FMT = 1
export PYTHONPATH := $(TB_DIR):/usr/local/lib/python3.11/site-packages/cocotb/share:$(PYTHONPATH)
export TOPLEVEL_LANG = verilog
export COCOTB_SHARE_DIR = $(shell cocotb-config --share)
export COCOTB_MAKEFILES = $(shell cocotb-config --makefiles)
export IVERILOG_VERSION = 12.0

# Default target
all: compile test

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)
	mkdir -p $(BUILD_DIR)/sim_build
	mkdir -p $(COVERAGE_DIR)

# Compile test program
$(TEST_ELF): $(TEST_ASM) | $(BUILD_DIR)
	$(RISCV_GCC) -march=rv32i -mabi=ilp32 -nostdlib -T$(TEST_DIR)/link.ld -o $@ $<

$(TEST_BIN): $(TEST_ELF)
	$(RISCV_OBJCOPY) -O binary $< $@

$(TEST_HEX): $(TEST_BIN)
	hexdump -v -e '/4 "%08x\n"' $< > $@

# Compile RTL
compile: $(BUILD_DIR)
	$(VERILATOR) --lint-only -Wall $(RTL_SRCS)

# Run all tests
test: compile $(TEST_HEX) test_units test_system

# Unit tests
test_units: test_alu test_register_file test_control_unit test_program_counter test_instruction_memory

# System test
test_system: $(RTL_SRCS) $(TB_DIR)/riscv_core_tb.sv $(TEST_HEX)
	$(IVERILOG) -g2012 -I$(RTL_DIR) -o $(BUILD_DIR)/riscv_core_tb.vvp $(RTL_SRCS) $(TB_DIR)/riscv_core_tb.sv
	cd $(BUILD_DIR) && vvp riscv_core_tb.vvp

# Individual unit tests
test_alu: $(RTL_DIR)/core/alu.sv $(TB_DIR)/test_alu.py | $(BUILD_DIR)
	rm -rf $(BUILD_DIR)/sim_build
	cd $(BUILD_DIR) && \
	PYTHONPATH=../$(TB_DIR):$(COCOTB_SHARE_DIR):$(PYTHONPATH) \
	MODULE=test_alu \
	TOPLEVEL=alu \
	VERILOG_SOURCES=../$(RTL_DIR)/core/alu.sv \
	make -f $(COCOTB_MAKEFILES)/Makefile.sim

test_register_file: $(RTL_DIR)/core/register_file.sv $(TB_DIR)/test_register_file.py | $(BUILD_DIR)
	rm -rf $(BUILD_DIR)/sim_build
	cd $(BUILD_DIR) && \
	PYTHONPATH=../$(TB_DIR):$(COCOTB_SHARE_DIR):$(PYTHONPATH) \
	MODULE=test_register_file \
	TOPLEVEL=register_file \
	VERILOG_SOURCES=../$(RTL_DIR)/core/register_file.sv \
	make -f $(COCOTB_MAKEFILES)/Makefile.sim

test_control_unit: $(RTL_DIR)/core/control_unit.sv $(TB_DIR)/test_control_unit.py | $(BUILD_DIR)
	rm -rf $(BUILD_DIR)/sim_build
	cd $(BUILD_DIR) && \
	PYTHONPATH=../$(TB_DIR):$(COCOTB_SHARE_DIR):$(PYTHONPATH) \
	MODULE=test_control_unit \
	TOPLEVEL=control_unit \
	VERILOG_SOURCES=../$(RTL_DIR)/core/control_unit.sv \
	SIM_BUILD=sim_build \
	IVERILOG_FLAGS="$(IVERILOG_COV_FLAGS)" \
	make -f $(COCOTB_MAKEFILES)/Makefile.sim

test_program_counter: $(RTL_DIR)/core/program_counter.sv $(TB_DIR)/test_program_counter.py | $(BUILD_DIR)
	rm -rf $(BUILD_DIR)/sim_build
	cd $(BUILD_DIR) && \
	PYTHONPATH=../$(TB_DIR):$(COCOTB_SHARE_DIR):$(PYTHONPATH) \
	MODULE=test_program_counter \
	TOPLEVEL=program_counter \
	VERILOG_SOURCES=../$(RTL_DIR)/core/program_counter.sv \
	make -f $(COCOTB_MAKEFILES)/Makefile.sim

test_instruction_memory: $(RTL_DIR)/memory/instruction_memory.sv $(TB_DIR)/test_instruction_memory.py | $(BUILD_DIR)
	rm -rf $(BUILD_DIR)/sim_build
	cd $(BUILD_DIR) && \
	PYTHONPATH=../$(TB_DIR):$(COCOTB_SHARE_DIR):$(PYTHONPATH) \
	MODULE=test_instruction_memory \
	TOPLEVEL=instruction_memory \
	VERILOG_SOURCES=../$(RTL_DIR)/memory/instruction_memory.sv \
	make -f $(COCOTB_MAKEFILES)/Makefile.sim

# Coverage report target
coverage: test
	@echo "Generating coverage report..."
	@mkdir -p $(COVERAGE_DIR)
	@find $(BUILD_DIR) -name "*.json" -exec cp {} $(COVERAGE_DIR)/ \;
	@$(PYTHON) $(TOOLS_DIR)/generate_coverage_report.py $(COVERAGE_DIR)

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)

.PHONY: all compile test test_units test_system test_alu test_register_file test_control_unit test_program_counter test_instruction_memory clean 