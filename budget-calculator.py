#!/usr/bin/env python3
"""
Summit Budget Calculator

Reads location data from locations.json and generates:
- Per-location cost breakdowns
- Comparison tables
- Exportable results for presentations

Usage:
    python budget-calculator.py                    # Full comparison
    python budget-calculator.py --location Lisbon  # Single location
    python budget-calculator.py --export csv       # Export to CSV
    python budget-calculator.py --export markdown  # Export to Markdown
"""

import json
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime


def load_locations(filepath: str = "locations.json") -> dict:
    """Load location data from JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Location file not found: {filepath}")

    with open(path, 'r') as f:
        return json.load(f)


def load_team_data(filepath: str = "team-locations.json") -> dict:
    """Load team location data from JSON file."""
    path = Path(filepath)
    if not path.exists():
        return None

    with open(path, 'r') as f:
        return json.load(f)


def load_visa_matrix(filepath: str = "visa-matrix.json") -> dict:
    """Load visa matrix from JSON file."""
    path = Path(filepath)
    if not path.exists():
        return None

    with open(path, 'r') as f:
        return json.load(f)


def calculate_location_cost(location: dict, team_size: int) -> dict:
    """Calculate total costs for a single location."""
    costs = location.get('cost_summary', {})

    # If cost_summary not pre-calculated, build from components
    if not costs.get('total_estimated'):
        flight_cost = location.get('flight_analysis', {}).get('avg_cost_per_person', 0) * team_size

        hotel_data = location.get('hotel_estimates', {})
        hotel_cost = (
            hotel_data.get('avg_nightly_rate', 0) *
            hotel_data.get('nights', 4) *
            hotel_data.get('rooms_needed', team_size)
        )

        venue_options = location.get('venue_options', [])
        venue_cost = venue_options[0].get('daily_rate', 0) * 3 if venue_options else 0

        catering_estimate = team_size * 50 * 3  # $50/person/day for 3 days
        ground_transport = team_size * 75  # $75/person for transfers

        subtotal = flight_cost + hotel_cost + venue_cost + catering_estimate + ground_transport
        contingency_pct = costs.get('contingency_pct', 10)
        contingency = subtotal * (contingency_pct / 100)

        costs = {
            'flights': flight_cost,
            'hotels': hotel_cost,
            'venue': venue_cost,
            'catering_estimate': catering_estimate,
            'ground_transport': ground_transport,
            'subtotal': subtotal,
            'contingency_pct': contingency_pct,
            'contingency': contingency,
            'total_estimated': subtotal + contingency
        }
    else:
        # Recalculate with contingency if needed
        subtotal = sum([
            costs.get('flights', 0),
            costs.get('hotels', 0),
            costs.get('venue', 0),
            costs.get('catering_estimate', 0),
            costs.get('ground_transport', 0)
        ])
        contingency_pct = costs.get('contingency_pct', 10)
        costs['subtotal'] = subtotal
        costs['contingency'] = subtotal * (contingency_pct / 100)
        costs['total_estimated'] = subtotal + costs['contingency']

    return costs


def generate_comparison_table(data: dict) -> list[dict]:
    """Generate comparison data for all locations."""
    team_size = data.get('metadata', {}).get('team_size', 40)
    results = []

    for location in data.get('locations', []):
        if not location.get('city'):
            continue

        costs = calculate_location_cost(location, team_size)

        results.append({
            'city': location.get('city'),
            'country': location.get('country'),
            'region': location.get('region'),
            'flights': costs.get('flights', 0),
            'hotels': costs.get('hotels', 0),
            'venue': costs.get('venue', 0),
            'catering': costs.get('catering_estimate', 0),
            'transport': costs.get('ground_transport', 0),
            'subtotal': costs.get('subtotal', 0),
            'contingency': costs.get('contingency', 0),
            'total': costs.get('total_estimated', 0),
            'visa_score': location.get('visa_complexity_score', 0),
            'flight_coverage': location.get('flight_analysis', {}).get('direct_flight_coverage_pct', 0),
            'pros': location.get('pros', []),
            'cons': location.get('cons', [])
        })

    # Sort by total cost
    results.sort(key=lambda x: x['total'])
    return results


def format_currency(amount: float) -> str:
    """Format number as currency."""
    return f"${amount:,.0f}"


def print_comparison_table(results: list[dict]) -> None:
    """Print formatted comparison table to console."""
    if not results:
        print("No locations to compare.")
        return

    print("\n" + "=" * 80)
    print("SUMMIT LOCATION COST COMPARISON")
    print("=" * 80 + "\n")

    # Header
    print(f"{'City':<20} {'Total Cost':>12} {'Visa Score':>10} {'Flight %':>10}")
    print("-" * 55)

    for r in results:
        print(f"{r['city']:<20} {format_currency(r['total']):>12} {r['visa_score']:>10} {r['flight_coverage']:>9}%")

    print("\n" + "-" * 80)
    print("DETAILED BREAKDOWN")
    print("-" * 80 + "\n")

    for r in results:
        if r['total'] == 0:
            continue

        print(f"\n{r['city']}, {r['country']} ({r['region']})")
        print("-" * 40)
        print(f"  Flights:        {format_currency(r['flights']):>12}")
        print(f"  Hotels:         {format_currency(r['hotels']):>12}")
        print(f"  Venue:          {format_currency(r['venue']):>12}")
        print(f"  Catering:       {format_currency(r['catering']):>12}")
        print(f"  Transport:      {format_currency(r['transport']):>12}")
        print(f"  {'─' * 25}")
        print(f"  Subtotal:       {format_currency(r['subtotal']):>12}")
        print(f"  Contingency:    {format_currency(r['contingency']):>12}")
        print(f"  {'═' * 25}")
        print(f"  TOTAL:          {format_currency(r['total']):>12}")

        if r['pros']:
            print(f"\n  Pros:")
            for pro in r['pros']:
                print(f"    + {pro}")

        if r['cons']:
            print(f"\n  Cons:")
            for con in r['cons']:
                print(f"    - {con}")


def export_to_csv(results: list[dict], filename: str = "budget-comparison.csv") -> None:
    """Export results to CSV file."""
    import csv

    with open(filename, 'w', newline='') as f:
        if not results:
            return

        fieldnames = ['city', 'country', 'region', 'flights', 'hotels', 'venue',
                      'catering', 'transport', 'subtotal', 'contingency', 'total',
                      'visa_score', 'flight_coverage']

        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    print(f"\nExported to {filename}")


def export_to_markdown(results: list[dict], filename: str = "budget-comparison.md") -> None:
    """Export results to Markdown file for presentations."""
    with open(filename, 'w') as f:
        f.write("# Summit Location Cost Comparison\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")

        # Summary table
        f.write("## Quick Comparison\n\n")
        f.write("| City | Total Cost | Visa Score | Direct Flights |\n")
        f.write("|------|-----------|------------|----------------|\n")

        for r in results:
            if r['total'] > 0:
                f.write(f"| {r['city']} | {format_currency(r['total'])} | {r['visa_score']}/5 | {r['flight_coverage']}% |\n")

        # Detailed sections
        f.write("\n## Detailed Breakdown\n\n")

        for r in results:
            if r['total'] == 0:
                continue

            f.write(f"### {r['city']}, {r['country']}\n\n")
            f.write(f"**Region:** {r['region']}\n\n")

            f.write("| Category | Cost |\n")
            f.write("|----------|------|\n")
            f.write(f"| Flights | {format_currency(r['flights'])} |\n")
            f.write(f"| Hotels | {format_currency(r['hotels'])} |\n")
            f.write(f"| Venue | {format_currency(r['venue'])} |\n")
            f.write(f"| Catering | {format_currency(r['catering'])} |\n")
            f.write(f"| Transport | {format_currency(r['transport'])} |\n")
            f.write(f"| **Subtotal** | **{format_currency(r['subtotal'])}** |\n")
            f.write(f"| Contingency | {format_currency(r['contingency'])} |\n")
            f.write(f"| **TOTAL** | **{format_currency(r['total'])}** |\n\n")

            if r['pros']:
                f.write("**Pros:**\n")
                for pro in r['pros']:
                    f.write(f"- {pro}\n")
                f.write("\n")

            if r['cons']:
                f.write("**Cons:**\n")
                for con in r['cons']:
                    f.write(f"- {con}\n")
                f.write("\n")

        # Recommendation placeholder
        f.write("## Recommendation\n\n")
        f.write("*[Add your recommendation based on RAPID framework analysis]*\n\n")
        f.write("### Decision Criteria Weights\n\n")
        f.write("- Total Cost: 35%\n")
        f.write("- Visa Complexity: 25%\n")
        f.write("- Flight Convenience: 20%\n")
        f.write("- Venue Quality: 10%\n")
        f.write("- Destination Appeal: 10%\n")

    print(f"\nExported to {filename}")


def analyze_single_location(data: dict, city_name: str) -> None:
    """Analyze and display details for a single location."""
    team_size = data.get('metadata', {}).get('team_size', 40)

    for location in data.get('locations', []):
        if location.get('city', '').lower() == city_name.lower():
            costs = calculate_location_cost(location, team_size)

            print(f"\n{'=' * 50}")
            print(f"ANALYSIS: {location['city']}, {location['country']}")
            print(f"{'=' * 50}\n")

            print(f"Team Size: {team_size}")
            print(f"Region: {location.get('region', 'N/A')}")
            print(f"Visa Complexity Score: {location.get('visa_complexity_score', 'N/A')}/5")

            print(f"\n{'Cost Breakdown':^40}")
            print("-" * 40)
            print(f"  Flights:        {format_currency(costs['flights']):>12}")
            print(f"  Hotels:         {format_currency(costs['hotels']):>12}")
            print(f"  Venue:          {format_currency(costs['venue']):>12}")
            print(f"  Catering:       {format_currency(costs['catering_estimate']):>12}")
            print(f"  Transport:      {format_currency(costs['ground_transport']):>12}")
            print(f"  {'─' * 30}")
            print(f"  Subtotal:       {format_currency(costs['subtotal']):>12}")
            print(f"  Contingency ({costs['contingency_pct']}%): {format_currency(costs['contingency']):>8}")
            print(f"  {'═' * 30}")
            print(f"  TOTAL:          {format_currency(costs['total_estimated']):>12}")

            # Per-person breakdown
            print(f"\n{'Per-Person Costs':^40}")
            print("-" * 40)
            print(f"  Flight avg:     {format_currency(costs['flights']/team_size):>12}")
            print(f"  Hotel:          {format_currency(costs['hotels']/team_size):>12}")
            print(f"  Other:          {format_currency((costs['venue']+costs['catering_estimate']+costs['ground_transport'])/team_size):>12}")
            print(f"  Total/person:   {format_currency(costs['total_estimated']/team_size):>12}")

            return

    print(f"Location '{city_name}' not found in data.")


def main():
    parser = argparse.ArgumentParser(description='Summit Budget Calculator')
    parser.add_argument('--location', '-l', type=str, help='Analyze a single location')
    parser.add_argument('--export', '-e', choices=['csv', 'markdown', 'both'],
                        help='Export results to file')
    parser.add_argument('--file', '-f', type=str, default='locations.json',
                        help='Path to locations JSON file')

    args = parser.parse_args()

    try:
        data = load_locations(args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure locations.json exists in the current directory.")
        return 1

    if args.location:
        analyze_single_location(data, args.location)
    else:
        results = generate_comparison_table(data)
        print_comparison_table(results)

        if args.export in ['csv', 'both']:
            export_to_csv(results)
        if args.export in ['markdown', 'both']:
            export_to_markdown(results)

    return 0


if __name__ == '__main__':
    exit(main())
