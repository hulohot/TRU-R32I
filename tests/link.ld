/* Simple linker script for RISC-V test program */
OUTPUT_ARCH( "riscv" )
ENTRY(_start)

MEMORY
{
  /* 4KB of instruction memory starting at 0x0 */
  imem (rx) : ORIGIN = 0x00000000, LENGTH = 4K
  /* 4KB of data memory starting at 0x1000 */
  dmem (rw) : ORIGIN = 0x00001000, LENGTH = 4K
}

SECTIONS
{
  /* Code section */
  .text : {
    *(.text)
  } > imem

  /* Read-only data */
  .rodata : {
    *(.rodata)
  } > imem

  /* Initialized data */
  .data : {
    *(.data)
  } > dmem

  /* Zero-initialized data */
  .bss : {
    *(.bss)
  } > dmem
} 