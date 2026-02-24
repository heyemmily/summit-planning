#!/usr/bin/env python3
"""Simple CLI wrapper for the Summit Planning skill.

This script loads the existing `budget-calculator.py` dynamically and exposes
the same analysis features programmatically for integration and testing.
"""
import argparse
import importlib.util
from importlib.machinery import SourceFileLoader
import os


def load_module():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    script_path = os.path.join(base_dir, "budget-calculator.py")
    loader = SourceFileLoader("budget_calc", script_path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description="Skill CLI for Summit Planning")
    parser.add_argument("--location", "-l", help="Analyze a single location")
    parser.add_argument("--export", "-e", choices=["csv", "markdown", "both"], help="Export results")
    parser.add_argument("--file", "-f", default="locations.json", help="Path to locations JSON file")

    args = parser.parse_args()

    mod = load_module()

    data = mod.load_locations(args.file)

    if args.location:
        # Print single location analysis
        mod.analyze_single_location(data, args.location)
    else:
        results = mod.generate_comparison_table(data)
        mod.print_comparison_table(results)

        if args.export in ("csv", "both"):
            mod.export_to_csv(results)
        if args.export in ("markdown", "both"):
            mod.export_to_markdown(results)


if __name__ == "__main__":
    main()
