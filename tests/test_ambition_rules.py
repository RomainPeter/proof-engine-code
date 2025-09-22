import json
from pathlib import Path

from pec_cli.ambition import apply_gap_rules, compile_obligations, render_proof_delta


def _ambition_base():
    return {
        "identity": "demo",
        "owners": ["@romain"],
        "compliance_targets": ["SOC2"],
        "api_stability": {"policy": "semver", "surface_paths": ["src/**/*.py"], "require_deprecation_cycle": True},
        "changelog": {"path": "CHANGELOG.md", "required_for": ["minor", "major", "breaking"]},
        "versioning": {"file": "pyproject.toml", "bump_rules": "auto"},
        "tests": {"min_coverage": 80, "required_suites": ["unit"]},
        "security": {"osv_gate": "high", "sast_paths": ["src/**"]},
        "reproducibility": {"lockfiles_required": ["requirements.txt"], "pinned_python": "3.11.9"},
        "provenance": {"sign_proof_journal": True, "artifact_retention_days": 180},
        "custom_obligations": []
    }


def test_apply_gap_rules_no_gaps():
    gaps, recs = apply_gap_rules(_ambition_base())
    assert not gaps
    assert "Activer provenance.sign_proof_journal" not in "\n".join(recs)


def test_compile_obligations_contains_expected():
    obligations = compile_obligations(_ambition_base())
    ids = {o["id"] for o in obligations}
    assert "OBL-API-BREAK" in ids
    assert "OBL-CHANGELOG" in ids
    assert "OBL-COVERAGE-THRESHOLD" in ids
    assert "OBL-OSV-GATE" in ids


def test_render_proof_delta_contains_sections():
    ambition = _ambition_base()
    obligations = compile_obligations(ambition)
    md = render_proof_delta(ambition, obligations)
    assert "API stability:" in md
    assert "Version bump:" in md
    assert "Changelog required for:" in md
