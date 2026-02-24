# Summit Planning System

[![CI](https://github.com/heyemmily/summit-planning/actions/workflows/ci.yml/badge.svg)](https://github.com/heyemmily/summit-planning/actions/workflows/ci.yml)

A structured system for planning global team summits with 40+ attendees from multiple countries.

## Quick Start

```bash
# 1. Update team data
# Edit team-locations.json with your attendee list

# 2. Research candidate cities
# Populate locations.json with your shortlist

# 3. Build visa matrix
# Fill in visa-matrix.json based on nationalities

# 4. Run budget analysis
python budget-calculator.py

# 5. Track progress
# Check off items in tasks.md as you complete them
```

## Files Overview

| File | Purpose | When to Update |
|------|---------|----------------|
| `tasks.md` | Master checklist for all phases | Daily during planning |
| `locations.json` | City comparison data | As you research each location |
| `team-locations.json` | Attendee tracking | When attendee list changes |
| `visa-matrix.json` | Visa requirements lookup | Once per planning cycle |
| `budget-calculator.py` | Cost analysis tool | Run after updating data |

## Workflow

### Phase 0: RAPID Research (Week 1-2)

1. **Populate `team-locations.json`**
   - Add all attendees with country, city, timezone
   - Flag visa restrictions by nationality

2. **Shortlist candidate cities in `locations.json`**
   - Start with 5-8 options
   - Add flight estimates from Google Flights
   - Get hotel quotes for group rates

3. **Build `visa-matrix.json`**
   - Cross-reference team nationalities with destinations
   - Mark advance visa requirements

4. **Run the calculator**
   ```bash
   python budget-calculator.py --export both
   ```

5. **Present to decision-makers** with generated reports

### Phase 1-5: See `tasks.md`

Follow the detailed checklists for planning, execution, and post-summit activities.

## Budget Calculator Usage

```bash
# View all locations compared
python budget-calculator.py

# Analyze a single city
python budget-calculator.py --location Lisbon

# Export for presentations
python budget-calculator.py --export csv       # Creates budget-comparison.csv
python budget-calculator.py --export markdown  # Creates budget-comparison.md
python budget-calculator.py --export both      # Both formats
```

## Data Entry Guide

### locations.json

```json
{
  "city": "City Name",
  "country": "Country",
  "flight_analysis": {
    "avg_cost_per_person": 850,      // Research via Google Flights
    "direct_flight_coverage_pct": 75  // % of team with direct flights
  },
  "hotel_estimates": {
    "avg_nightly_rate": 180,          // Group rate quote
    "nights": 4
  },
  "visa_complexity_score": 2,         // 1-5 scale (see scoring guide)
  "pros": ["..."],
  "cons": ["..."]
}
```

### team-locations.json

```json
{
  "country": "Country Name",
  "count": 5,                         // Number of attendees
  "nearest_hub_airport": "XXX",       // 3-letter code
  "visa_restrictions": {
    "has_restrictions": true,
    "restricted_destinations": ["Schengen", "UK"]
  }
}
```

### visa-matrix.json

Use these requirement codes:
- `visa_free` - No visa required
- `visa_on_arrival` - Get visa at airport
- `e_visa` - Apply online before travel
- `advance_visa` - Embassy appointment required

## Scoring Guide

### Visa Complexity Score (1-5)

| Score | Meaning |
|-------|---------|
| 1 | No visa required for any team member |
| 2 | Some visa-on-arrival, no advance visas |
| 3 | 1-5 people need advance visas |
| 4 | 6-10 people need advance visas |
| 5 | 10+ need advance visas or complex requirements |

### Decision Weights (Default)

- **Total Cost:** 35%
- **Visa Complexity:** 25%
- **Flight Convenience:** 20%
- **Venue Quality:** 10%
- **Destination Appeal:** 10%

Adjust weights in `locations.json` under `scoring_criteria.weights`.

## Tips

- **Start visa research early** - Some visas take 4-6 weeks
- **Get 3 hotel quotes** per city for negotiating leverage
- **Check flight prices** on Tuesday/Wednesday for best estimates
- **Update data weekly** during active research phase
- **Archive final data** for future summit planning

## RAPID Framework Reference

- **R**ecommend: Planner proposes options
- **A**gree: Stakeholders align on criteria
- **P**erform: Team executes research
- **I**nput: Gather data from all sources
- **D**ecide: Decision-maker selects location

---

*Need help? Check `tasks.md` for the current phase and next actions.*

## Skill Integration

This repository includes a small Claude Code / skill wrapper in the `skill/` folder that
exposes the functionality of `budget-calculator.py` via an HTTP endpoint and a CLI wrapper.

- See `skill/README_SKILL.md` for quick start instructions to run the FastAPI skill server.
- Example request payloads are in the `examples/` folder.

If you want deeper research assistance (flight scouting, hotel sourcing, visa research),
consider integrating dedicated research skills. A helpful reference implementation is:
https://github.com/Weizhena/Deep-Research-skills/tree/master/skills/research-en

