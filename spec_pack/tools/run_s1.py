import os
import subprocess
import sys
import json
from xml.etree import ElementTree


def _read_coverage_percent(cobertura_path: str) -> float | None:
    try:
        tree = ElementTree.parse(cobertura_path)
        root = tree.getroot()
        # Cobertura: attributes line-rate or lines-valid/lines-covered
        line_rate = root.attrib.get("line-rate")
        if line_rate is not None:
            return float(line_rate) * 100.0
        lines_valid = root.attrib.get("lines-valid")
        lines_covered = root.attrib.get("lines-covered")
        if lines_valid and lines_covered:
            valid = float(lines_valid)
            covered = float(lines_covered)
            if valid > 0:
                return (covered / valid) * 100.0
    except Exception:
        return None
    return None


def _enforce_obligations(obligations_path: str) -> None:
    if not os.path.isfile(obligations_path):
        print(f"[run_s1] No obligations file at {obligations_path}; skipping enforcement")
        return
    try:
        obligations = json.loads(open(obligations_path, "r", encoding="utf-8").read())
    except Exception as exc:
        print(f"[run_s1] Failed to read obligations: {exc}")
        return

    # Coverage threshold enforcement
    cov_obl = next((o for o in obligations if o.get("id") == "OBL-COVERAGE-THRESHOLD"), None)
    if cov_obl:
        threshold = float(cov_obl.get("threshold", 0))
        cobertura_candidates = [
            os.environ.get("COVERAGE_XML", "coverage.xml"),
            os.path.join(".proof", "coverage.xml"),
        ]
        coverage_value = None
        for path in cobertura_candidates:
            if os.path.isfile(path):
                coverage_value = _read_coverage_percent(path)
                if coverage_value is not None:
                    break
        if coverage_value is None:
            print("[run_s1] Coverage report not found or unreadable; skipping coverage enforcement")
        else:
            print(f"[run_s1] Coverage: {coverage_value:.1f}% (threshold {threshold:.1f}%)")
            if coverage_value + 1e-9 < threshold:
                print("[run_s1] Coverage below threshold; failing the job")
                sys.exit(1)


def main():
    journal = os.environ.get("PROOF_JOURNAL", ".proof/journal.ndjson")
    merkle = os.environ.get("PROOF_MERKLE", ".proof/merkle.json")
    obligations_path = os.environ.get("PEC_OBLIGATIONS_PATH", ".pec/obligations.lock")

    # Enforce obligations (coverage etc.) before running verification
    _enforce_obligations(obligations_path)

    cmd = [
        sys.executable,
        "spec_pack/tools/verify.py",
        "--journal",
        journal,
        "--merkle-root-file",
        merkle,
    ]
    print("Running S1 audit checks (journal + merkle verify)…")
    rc = subprocess.run(cmd, check=False).returncode
    sys.exit(rc)


if __name__ == "__main__":
    main()
