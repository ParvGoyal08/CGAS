r"""P4: every gold example validates (schema + engine replay); every file under invalid/ is rejected."""
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_all_gold_examples_behave_as_expected():
    r = subprocess.run([sys.executable, str(ROOT / "tools/validate_gold.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]
