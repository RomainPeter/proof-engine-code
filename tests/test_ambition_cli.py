import json
from pathlib import Path
from typer.testing import CliRunner

from pec_cli.__main__ import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ambition" in result.stdout


def test_ambition_validate_compile(tmp_path: Path, monkeypatch):
    # Créer un repo temporaire avec .pec/ambition.json minimal
    d = tmp_path
    pec_dir = d / ".pec"
    pec_dir.mkdir()
    ambition = {
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
    (pec_dir / "ambition.json").write_text(json.dumps(ambition), encoding="utf-8")

    # Se placer dans le tmp
    monkeypatch.chdir(d)
    runner = CliRunner()

    # validate
    res_v = runner.invoke(app, ["ambition", "validate"])
    assert res_v.exit_code == 0
    assert "OK" in res_v.stdout

    # compile
    res_c = runner.invoke(app, ["ambition", "compile"])
    assert res_c.exit_code == 0
    assert (pec_dir / "obligations.lock").exists()
    assert (pec_dir / "proof_delta.md").exists()
