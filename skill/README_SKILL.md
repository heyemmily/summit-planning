# Summit Planning Skill

[![CI](https://github.com/heyemmily/summit-planning/actions/workflows/ci.yml/badge.svg)](https://github.com/heyemmily/summit-planning/actions/workflows/ci.yml)

This folder contains a small Claude Code skill wrapper around the existing
`budget-calculator.py` tool. It includes a FastAPI server and a CLI wrapper so
the functionality can be called programmatically by a skill runtime.

Quick start

1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the HTTP skill server:

```bash
uvicorn skill.skill_server:app --reload --port 8000
```

3. Call the endpoint:

```bash
curl -X POST http://localhost:8000/compare -H "Content-Type: application/json" -d '{"file":"locations.json"}'
```

4. Or run the CLI locally:

```bash
python skill/cli.py --export both
```

Notes
- The server dynamically loads `budget-calculator.py` from the repository root so
  the original code doesn't need to be renamed.
- The `skill_spec.yaml` file contains example intents and endpoint info for
  turning this into a Claude Code / Anthropics skill bundle.
