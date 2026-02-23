import subprocess
import sys
import os


def test_cli_runs_full_export(tmp_path):
    # Run the CLI to produce exports (writes files to repo root)
    cmd = [sys.executable, os.path.join("skill", "cli.py"), "--export", "both", "--file", "locations.json"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 0, f"CLI failed: {proc.stderr}"


def test_cli_single_location(tmp_path):
    cmd = [sys.executable, os.path.join("skill", "cli.py"), "--location", "Lisbon", "--file", "locations.json"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 0, f"CLI single location failed: {proc.stderr}"
