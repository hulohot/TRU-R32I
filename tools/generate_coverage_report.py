#!/usr/bin/env python3

import json
import os
import sys
from collections import defaultdict
from datetime import datetime

class CoverageReportGenerator:
    def __init__(self, coverage_dir):
        self.coverage_dir = coverage_dir
        self.total_coverage = defaultdict(lambda: {"covered": 0, "total": 0})
        self.module_coverage = defaultdict(lambda: defaultdict(lambda: {"covered": 0, "total": 0}))

    def load_coverage_data(self):
        """Load all JSON coverage files from the coverage directory."""
        for filename in os.listdir(self.coverage_dir):
            if filename.endswith('.json'):
                module_name = filename.replace('coverage_', '').replace('.json', '')
                with open(os.path.join(self.coverage_dir, filename), 'r') as f:
                    try:
                        data = json.load(f)
                        self.process_module_coverage(module_name, data)
                    except json.JSONDecodeError:
                        print(f"Error: Could not parse {filename}")

    def process_module_coverage(self, module_name, data):
        """Process coverage data for a single module."""
        # Process instruction types
        if "instruction_types" in data:
            for instr, count in data["instruction_types"].items():
                self.module_coverage[module_name]["instructions"][instr] = {
                    "covered": count > 0,
                    "total": 1
                }
                self.total_coverage["instructions"]["covered"] += (1 if count > 0 else 0)
                self.total_coverage["instructions"]["total"] += 1

        # Process control signals
        if "control_signals" in data:
            for signal, count in data["control_signals"].items():
                self.module_coverage[module_name]["signals"][signal] = {
                    "covered": count > 0,
                    "total": 1
                }
                self.total_coverage["signals"]["covered"] += (1 if count > 0 else 0)
                self.total_coverage["signals"]["total"] += 1

        # Process register usage
        if "register_usage" in data:
            for reg, count in data["register_usage"].items():
                self.module_coverage[module_name]["registers"][reg] = {
                    "covered": count > 0,
                    "total": 1
                }
                self.total_coverage["registers"]["covered"] += (1 if count > 0 else 0)
                self.total_coverage["registers"]["total"] += 1

    def generate_report(self):
        """Generate a comprehensive coverage report."""
        report = []
        report.append("RISC-V CPU Coverage Report")
        report.append("=" * 50)
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Overall coverage summary
        report.append("Overall Coverage Summary")
        report.append("-" * 30)
        for category, data in self.total_coverage.items():
            percentage = (data["covered"] / data["total"] * 100) if data["total"] > 0 else 0
            report.append(f"{category.title()}: {percentage:.2f}% ({data['covered']}/{data['total']})")
        report.append("")

        # Module-specific coverage
        for module, categories in self.module_coverage.items():
            report.append(f"Module: {module}")
            report.append("-" * (len(module) + 8))
            
            for category, items in categories.items():
                covered = sum(1 for item in items.values() if item["covered"])
                total = len(items)
                percentage = (covered / total * 100) if total > 0 else 0
                report.append(f"\n{category.title()} Coverage: {percentage:.2f}% ({covered}/{total})")
                
                # Detailed coverage for each item
                for item, data in items.items():
                    status = "✓" if data["covered"] else "✗"
                    report.append(f"  {status} {item}")
            report.append("\n" + "=" * 50 + "\n")

        return "\n".join(report)

    def save_report(self, output_file="coverage_report.txt"):
        """Save the coverage report to a file."""
        report = self.generate_report()
        with open(os.path.join(self.coverage_dir, output_file), 'w') as f:
            f.write(report)
        print(f"Coverage report saved to {os.path.join(self.coverage_dir, output_file)}")
        print("\nSummary:")
        print(report.split("\nModule:")[0])  # Print just the summary section

def main():
    if len(sys.argv) != 2:
        print("Usage: generate_coverage_report.py <coverage_directory>")
        sys.exit(1)

    coverage_dir = sys.argv[1]
    if not os.path.isdir(coverage_dir):
        print(f"Error: {coverage_dir} is not a directory")
        sys.exit(1)

    generator = CoverageReportGenerator(coverage_dir)
    generator.load_coverage_data()
    generator.save_report()

if __name__ == "__main__":
    main() 