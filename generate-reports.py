#!/usr/bin/env python3
"""
Summit Report Generator for Notion

Generates Notion-ready markdown reports from data files.
Can run once or watch for changes and auto-regenerate.

Usage:
    python generate-reports.py                    # Generate all reports once
    python generate-reports.py --watch            # Watch files and auto-regenerate
    python generate-reports.py --report team      # Generate specific report
    python generate-reports.py --output notion/   # Output to specific directory
"""

import json
import argparse
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Output directory for generated reports
DEFAULT_OUTPUT_DIR = "reports"

# Files to watch for changes
WATCH_FILES = [
    "team-locations.json",
    "visa-matrix.json",
    "locations.json"
]


def load_json(filepath: str) -> Optional[dict]:
    """Load JSON file, return None if not found."""
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return json.load(f)


def ensure_output_dir(output_dir: str) -> None:
    """Create output directory if it doesn't exist."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def generate_header(title: str) -> str:
    """Generate Notion-friendly header with metadata."""
    return f"""# {title}

> **Auto-generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
> **Source:** Summit Planning System

---

"""


def generate_team_report(output_dir: str) -> str:
    """Generate team locations report for Notion."""
    data = load_json("team-locations.json")
    if not data:
        return None

    output_path = Path(output_dir) / "team-overview.md"

    content = generate_header("Team Overview")

    metadata = data.get('metadata', {})
    content += f"""## Summary

| Metric | Value |
|--------|-------|
| Total Attendees | {metadata.get('total_attendees', 'TBD')} |
| Countries | {metadata.get('total_countries', 'TBD')} |
| Last Updated | {metadata.get('last_updated', 'N/A')} |

"""

    # Regional breakdown
    content += "## By Region\n\n"

    regions = {}
    for country in data.get('countries', []):
        region = country.get('region', 'Unknown')
        if region not in regions:
            regions[region] = {'count': 0, 'countries': []}
        regions[region]['count'] += country.get('count', 0)
        regions[region]['countries'].append(country)

    for region, info in sorted(regions.items(), key=lambda x: -x[1]['count']):
        content += f"### {region} ({info['count']} people)\n\n"
        content += "| Country | Count | Hub Airport | Timezone |\n"
        content += "|---------|-------|-------------|----------|\n"

        for country in sorted(info['countries'], key=lambda x: -x.get('count', 0)):
            content += f"| {country.get('country', '')} | {country.get('count', 0)} | {country.get('nearest_hub_airport', '')} | {country.get('timezone', '')} |\n"

        content += "\n"

    # Visa restrictions summary
    restricted = [c for c in data.get('countries', [])
                  if c.get('visa_restrictions', {}).get('has_restrictions')]

    if restricted:
        content += "## Visa Restrictions Flag\n\n"
        content += "These team members may need advance visas depending on destination:\n\n"
        content += "| Country | Count | Restricted From |\n"
        content += "|---------|-------|------------------|\n"

        for country in restricted:
            restrictions = country.get('visa_restrictions', {}).get('restricted_destinations', [])
            content += f"| {country.get('country', '')} | {country.get('count', 0)} | {', '.join(restrictions)} |\n"

        content += "\n"

    # Timezone distribution for meeting planning
    content += "## Timezone Distribution\n\n"
    content += "For planning synchronous sessions:\n\n"

    tz_groups = {}
    for country in data.get('countries', []):
        tz = country.get('timezone', 'Unknown')
        if tz not in tz_groups:
            tz_groups[tz] = 0
        tz_groups[tz] += country.get('count', 0)

    content += "| Timezone | Attendees |\n"
    content += "|----------|----------|\n"
    for tz, count in sorted(tz_groups.items()):
        content += f"| {tz} | {count} |\n"

    content += "\n---\n*Copy this content directly into Notion*\n"

    with open(output_path, 'w') as f:
        f.write(content)

    return str(output_path)


def generate_visa_report(output_dir: str) -> str:
    """Generate visa matrix report for Notion."""
    data = load_json("visa-matrix.json")
    if not data:
        return None

    output_path = Path(output_dir) / "visa-matrix.md"

    content = generate_header("Visa Requirements Matrix")

    metadata = data.get('metadata', {})
    content += f"""## Overview

| Detail | Value |
|--------|-------|
| Team Nationalities | {metadata.get('team_nationalities_count', 'TBD')} |
| Candidate Cities | {metadata.get('candidate_cities_count', 'TBD')} |
| Last Updated | {metadata.get('last_updated', 'N/A')} |

### Requirement Legend

| Code | Meaning | Lead Time |
|------|---------|-----------|
| ✅ visa_free | No visa required | None |
| 🟡 visa_on_arrival | Get at airport | None |
| 🟠 e_visa | Apply online | 3-7 days |
| 🔴 advance_visa | Embassy required | 2-6 weeks |

"""

    # Matrix table
    destinations = data.get('destinations', {})
    nationalities = data.get('nationalities', [])

    if destinations and nationalities:
        content += "## Requirements by Destination\n\n"

        for dest_name, dest_info in destinations.items():
            content += f"### {dest_name}\n\n"

            # Group by requirement type
            groups = {
                'visa_free': [],
                'visa_on_arrival': [],
                'e_visa': [],
                'advance_visa': []
            }

            requirements = dest_info.get('requirements', {})
            for nat in nationalities:
                nat_name = nat.get('nationality', '')
                req = requirements.get(nat_name, {})
                req_type = req.get('type', 'unknown')
                if req_type in groups:
                    groups[req_type].append({
                        'nationality': nat_name,
                        'count': nat.get('count', 0),
                        'processing_days': req.get('processing_days', 0),
                        'notes': req.get('notes', '')
                    })

            # Summary counts
            content += f"| Requirement | Nationalities | People Affected |\n"
            content += f"|-------------|---------------|------------------|\n"
            content += f"| ✅ Visa Free | {len(groups['visa_free'])} | {sum(n['count'] for n in groups['visa_free'])} |\n"
            content += f"| 🟡 On Arrival | {len(groups['visa_on_arrival'])} | {sum(n['count'] for n in groups['visa_on_arrival'])} |\n"
            content += f"| 🟠 E-Visa | {len(groups['e_visa'])} | {sum(n['count'] for n in groups['e_visa'])} |\n"
            content += f"| 🔴 Advance | {len(groups['advance_visa'])} | {sum(n['count'] for n in groups['advance_visa'])} |\n"
            content += "\n"

            # Detail for advance visas (most critical)
            if groups['advance_visa']:
                content += "**Advance Visa Required:**\n\n"
                content += "| Nationality | People | Processing Time | Notes |\n"
                content += "|-------------|--------|-----------------|-------|\n"
                for nat in groups['advance_visa']:
                    content += f"| {nat['nationality']} | {nat['count']} | {nat['processing_days']} days | {nat['notes']} |\n"
                content += "\n"

            content += "---\n\n"

    # Complexity scoring
    content += "## Destination Visa Complexity Scores\n\n"
    content += "Lower is better (fewer advance visas needed):\n\n"
    content += "| Destination | Complexity Score | Advance Visas Needed |\n"
    content += "|-------------|------------------|----------------------|\n"

    for dest_name, dest_info in destinations.items():
        score = dest_info.get('complexity_score', 0)
        advance_count = sum(1 for req in dest_info.get('requirements', {}).values()
                          if req.get('type') == 'advance_visa')
        content += f"| {dest_name} | {score}/5 | {advance_count} |\n"

    content += "\n---\n*Copy this content directly into Notion*\n"

    with open(output_path, 'w') as f:
        f.write(content)

    return str(output_path)


def generate_locations_report(output_dir: str) -> str:
    """Generate locations comparison report for Notion."""
    data = load_json("locations.json")
    if not data:
        return None

    output_path = Path(output_dir) / "location-comparison.md"

    content = generate_header("Location Comparison")

    metadata = data.get('metadata', {})
    team_size = metadata.get('team_size', 40)

    content += f"""## Planning Parameters

| Parameter | Value |
|-----------|-------|
| Team Size | {team_size} |
| Summit Duration | {metadata.get('summit_duration_days', 3)} days |
| Target Dates | {metadata.get('target_dates', 'TBD')} |

"""

    # Quick comparison table
    locations = data.get('locations', [])
    if locations:
        content += "## Quick Comparison\n\n"
        content += "| City | Est. Total | Visa Score | Direct Flights | Recommendation |\n"
        content += "|------|-----------|------------|----------------|----------------|\n"

        for loc in sorted(locations, key=lambda x: x.get('cost_summary', {}).get('total_estimated', 999999)):
            total = loc.get('cost_summary', {}).get('total_estimated', 0)
            visa = loc.get('visa_complexity_score', 0)
            flights = loc.get('flight_analysis', {}).get('direct_flight_coverage_pct', 0)

            # Simple recommendation indicator
            if visa <= 2 and flights >= 70:
                rec = "⭐ Strong"
            elif visa <= 3 and flights >= 50:
                rec = "👍 Good"
            else:
                rec = "⚠️ Consider"

            content += f"| {loc.get('city', '')} | ${total:,.0f} | {visa}/5 | {flights}% | {rec} |\n"

        content += "\n"

        # Detailed breakdown per location
        content += "## Detailed Breakdown\n\n"

        for loc in locations:
            city = loc.get('city', 'Unknown')
            country = loc.get('country', '')

            content += f"### {city}, {country}\n\n"

            # Pros and cons in callout format (Notion-friendly)
            pros = loc.get('pros', [])
            cons = loc.get('cons', [])

            if pros:
                content += "> **Pros**\n"
                for pro in pros:
                    content += f"> - {pro}\n"
                content += "\n"

            if cons:
                content += "> **Cons**\n"
                for con in cons:
                    content += f"> - {con}\n"
                content += "\n"

            # Cost breakdown
            costs = loc.get('cost_summary', {})
            content += "**Cost Breakdown:**\n\n"
            content += "| Category | Amount |\n"
            content += "|----------|--------|\n"
            content += f"| Flights | ${costs.get('flights', 0):,.0f} |\n"
            content += f"| Hotels | ${costs.get('hotels', 0):,.0f} |\n"
            content += f"| Venue | ${costs.get('venue', 0):,.0f} |\n"
            content += f"| Catering | ${costs.get('catering_estimate', 0):,.0f} |\n"
            content += f"| Transport | ${costs.get('ground_transport', 0):,.0f} |\n"
            content += f"| **Subtotal** | **${costs.get('subtotal', 0):,.0f}** |\n"
            content += f"| Contingency ({costs.get('contingency_pct', 10)}%) | ${costs.get('contingency', 0):,.0f} |\n"
            content += f"| **TOTAL** | **${costs.get('total_estimated', 0):,.0f}** |\n"
            content += "\n"

            # Venue options
            venues = loc.get('venue_options', [])
            if venues:
                content += "**Venue Options:**\n\n"
                for venue in venues:
                    content += f"- **{venue.get('name', '')}** - ${venue.get('daily_rate', 0):,}/day, capacity {venue.get('capacity', 'N/A')}\n"
                content += "\n"

            content += "---\n\n"

    content += "*Copy this content directly into Notion*\n"

    with open(output_path, 'w') as f:
        f.write(content)

    return str(output_path)


def generate_executive_summary(output_dir: str) -> str:
    """Generate consolidated executive summary for Notion."""
    team_data = load_json("team-locations.json")
    visa_data = load_json("visa-matrix.json")
    location_data = load_json("locations.json")

    output_path = Path(output_dir) / "executive-summary.md"

    content = generate_header("Summit Planning Executive Summary")

    # Team overview
    content += "## Team Overview\n\n"
    if team_data:
        meta = team_data.get('metadata', {})
        content += f"- **Total Attendees:** {meta.get('total_attendees', 'TBD')}\n"
        content += f"- **Countries Represented:** {meta.get('total_countries', 'TBD')}\n"

        # Regional breakdown
        regions = {}
        for country in team_data.get('countries', []):
            region = country.get('region', 'Unknown')
            regions[region] = regions.get(region, 0) + country.get('count', 0)

        content += "- **Regional Distribution:**\n"
        for region, count in sorted(regions.items(), key=lambda x: -x[1]):
            content += f"  - {region}: {count}\n"
    else:
        content += "*Team data not yet populated*\n"

    content += "\n"

    # Location recommendations
    content += "## Location Recommendations\n\n"
    if location_data:
        locations = location_data.get('locations', [])

        # Sort by total cost
        sorted_locs = sorted(locations,
                            key=lambda x: x.get('cost_summary', {}).get('total_estimated', 999999))

        content += "| Rank | City | Total Cost | Visa | Flights | Status |\n"
        content += "|------|------|-----------|------|---------|--------|\n"

        for i, loc in enumerate(sorted_locs[:5], 1):
            total = loc.get('cost_summary', {}).get('total_estimated', 0)
            visa = loc.get('visa_complexity_score', 0)
            flights = loc.get('flight_analysis', {}).get('direct_flight_coverage_pct', 0)

            status = "🟢" if visa <= 2 and flights >= 60 else "🟡" if visa <= 3 else "🔴"

            content += f"| {i} | {loc.get('city', '')} | ${total:,.0f} | {visa}/5 | {flights}% | {status} |\n"
    else:
        content += "*Location data not yet populated*\n"

    content += "\n"

    # Visa complexity
    content += "## Visa Considerations\n\n"
    if visa_data:
        destinations = visa_data.get('destinations', {})

        content += "| Destination | Complexity | Advance Visas |\n"
        content += "|-------------|------------|---------------|\n"

        for dest, info in sorted(destinations.items(),
                                 key=lambda x: x[1].get('complexity_score', 5)):
            score = info.get('complexity_score', 0)
            advance = sum(1 for r in info.get('requirements', {}).values()
                         if r.get('type') == 'advance_visa')
            content += f"| {dest} | {score}/5 | {advance} people |\n"
    else:
        content += "*Visa matrix not yet populated*\n"

    content += "\n"

    # Decision framework
    content += """## RAPID Decision Framework

| Role | Person | Status |
|------|--------|--------|
| **R**ecommend | [Planner] | Preparing options |
| **A**gree | [Stakeholders] | Pending |
| **P**erform | [Team] | Research in progress |
| **I**nput | [All sources] | Gathering data |
| **D**ecide | [Decision maker] | Awaiting recommendation |

## Next Steps

- [ ] Complete team location data
- [ ] Finalize candidate city research
- [ ] Build visa matrix
- [ ] Run cost comparison
- [ ] Present recommendation

"""

    content += "---\n*Copy this content directly into Notion*\n"

    with open(output_path, 'w') as f:
        f.write(content)

    return str(output_path)


def generate_all_reports(output_dir: str) -> list[str]:
    """Generate all reports."""
    ensure_output_dir(output_dir)

    generated = []

    reports = [
        ("Team Overview", generate_team_report),
        ("Visa Matrix", generate_visa_report),
        ("Location Comparison", generate_locations_report),
        ("Executive Summary", generate_executive_summary),
    ]

    for name, generator in reports:
        try:
            path = generator(output_dir)
            if path:
                generated.append(path)
                print(f"✓ Generated: {path}")
            else:
                print(f"⚠ Skipped {name}: source data not found")
        except Exception as e:
            print(f"✗ Error generating {name}: {e}")

    return generated


def get_file_mtimes() -> dict:
    """Get modification times of watched files."""
    mtimes = {}
    for filepath in WATCH_FILES:
        path = Path(filepath)
        if path.exists():
            mtimes[filepath] = path.stat().st_mtime
    return mtimes


def watch_and_regenerate(output_dir: str, interval: int = 2) -> None:
    """Watch for file changes and regenerate reports."""
    print(f"\n👀 Watching for changes in: {', '.join(WATCH_FILES)}")
    print(f"📁 Output directory: {output_dir}")
    print("Press Ctrl+C to stop\n")

    last_mtimes = get_file_mtimes()

    # Initial generation
    print("=" * 50)
    print("Initial generation...")
    generate_all_reports(output_dir)
    print("=" * 50 + "\n")

    try:
        while True:
            time.sleep(interval)
            current_mtimes = get_file_mtimes()

            changed = []
            for filepath, mtime in current_mtimes.items():
                if filepath not in last_mtimes or mtime > last_mtimes[filepath]:
                    changed.append(filepath)

            if changed:
                print(f"\n🔄 Detected changes in: {', '.join(changed)}")
                print("-" * 50)
                generate_all_reports(output_dir)
                print("-" * 50)
                print(f"✅ Reports updated at {datetime.now().strftime('%H:%M:%S')}\n")
                last_mtimes = current_mtimes

    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching.")


def main():
    parser = argparse.ArgumentParser(description='Generate Notion-ready summit reports')
    parser.add_argument('--watch', '-w', action='store_true',
                        help='Watch files and auto-regenerate on changes')
    parser.add_argument('--output', '-o', type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--report', '-r',
                        choices=['team', 'visa', 'locations', 'summary', 'all'],
                        default='all',
                        help='Generate specific report (default: all)')

    args = parser.parse_args()

    if args.watch:
        watch_and_regenerate(args.output)
    else:
        ensure_output_dir(args.output)

        if args.report == 'all':
            generate_all_reports(args.output)
        elif args.report == 'team':
            path = generate_team_report(args.output)
            print(f"Generated: {path}" if path else "Team data not found")
        elif args.report == 'visa':
            path = generate_visa_report(args.output)
            print(f"Generated: {path}" if path else "Visa data not found")
        elif args.report == 'locations':
            path = generate_locations_report(args.output)
            print(f"Generated: {path}" if path else "Location data not found")
        elif args.report == 'summary':
            path = generate_executive_summary(args.output)
            print(f"Generated: {path}" if path else "No data found")

        print(f"\n📋 Reports ready in: {args.output}/")
        print("Copy the markdown content directly into Notion pages.")


if __name__ == '__main__':
    main()
