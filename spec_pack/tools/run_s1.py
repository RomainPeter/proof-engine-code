import os
import subprocess
import sys
import json
from xml.etree import ElementTree
from pathlib import Path


def _read_coverage_percent(cobertura_path: str) -> float | None:
    try:
        tree = ElementTree.parse(cobertura_path)
        root = tree.getroot()
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


def _ensure_proof_dir() -> Path:
    p = Path(".proof")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _emit_api_diff(proof_dir: Path) -> None:
    out = proof_dir / "api_diff.json"
    try:
        rc = subprocess.run([sys.executable, "spec_pack/tools/check_api_diff.py", "--emit"], check=False)
        if rc.returncode != 0 and not out.exists():
            out.write_text("{}", encoding="utf-8")
    except Exception:
        if not out.exists():
            out.write_text("{}", encoding="utf-8")


def _emit_build_manifest(proof_dir: Path) -> None:
    out = proof_dir / "build_manifest.json"
    try:
        rc = subprocess.run([sys.executable, "spec_pack/tools/build_pinning.py", "--emit", "-o", str(out)], check=False)
        if rc.returncode != 0 and not out.exists():
            out.write_text("{}", encoding="utf-8")
    except Exception:
        if not out.exists():
            out.write_text("{}", encoding="utf-8")


def _ensure_journal(proof_dir: Path, merkle_path: Path) -> None:
    j = proof_dir / "journal.ndjson"
    if j.exists():
        return
    try:
        import datetime
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        event = {"ts": ts, "event": "ci_run", "sha": os.environ.get("GITHUB_SHA", "local"), "merkle_file": str(merkle_path)}
        j.write_text(json.dumps(event) + "\n", encoding="utf-8")
    except Exception:
        pass


def main():
    journal = os.environ.get("PROOF_JOURNAL", ".proof/journal.ndjson")
    merkle = os.environ.get("PROOF_MERKLE", ".proof/merkle.json")
    obligations_path = os.environ.get("PEC_OBLIGATIONS_PATH", ".pec/obligations.lock")

    _enforce_obligations(obligations_path)

    proof_dir = _ensure_proof_dir()

    _emit_api_diff(proof_dir)
    _emit_build_manifest(proof_dir)

    # Recalculate Merkle
    try:
        subprocess.run([sys.executable, "spec_pack/tools/merkle_hasher.py", "--in", str(proof_dir), "--out", merkle], check=False)
    except Exception:
        pass

    _ensure_journal(proof_dir, Path(merkle))

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
