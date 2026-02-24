import importlib.util
from importlib.machinery import SourceFileLoader
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Summit Planning Skill")


def load_budget_module():
    """Dynamically load the existing budget-calculator.py script as a module.

    Uses SourceFileLoader so we don't have to rename the original file.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    script_path = os.path.join(base_dir, "budget-calculator.py")

    if not os.path.exists(script_path):
        raise FileNotFoundError("budget-calculator.py not found in repository root")

    loader = SourceFileLoader("budget_calc", script_path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class CompareRequest(BaseModel):
    file: Optional[str] = "locations.json"
    export: Optional[str] = None  # csv | markdown | both
    location: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/compare")
def compare(req: CompareRequest):
    try:
        mod = load_budget_module()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    # Load data
    try:
        data = mod.load_locations(req.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load data: {e}") from e

    if req.location:
        results = mod.generate_comparison_table(data)
        for r in results:
            if r.get("city", "").lower() == req.location.lower():
                return {"location": r}
        raise HTTPException(status_code=404, detail="Location not found")

    # Full comparison
    results = mod.generate_comparison_table(data)

    # Optionally export files into repo root
    if req.export in ("csv", "both"):
        try:
            mod.export_to_csv(results)
        except Exception:
            pass
    if req.export in ("markdown", "both"):
        try:
            mod.export_to_markdown(results)
        except Exception:
            pass

    return {"results": results}
