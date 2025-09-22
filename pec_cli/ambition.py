import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import typer
from rich import print
from jsonschema import Draft202012Validator

DEFAULTS = {
  "owners": ["@romain"],
  "api_stability": {
    "policy": "semver",
    "surface_paths": ["src/**/*.py"],
    "require_deprecation_cycle": True,
  },
  "changelog": {"path": "CHANGELOG.md", "required_for": ["minor", "major", "breaking"]},
  "versioning": {"file": "pyproject.toml", "bump_rules": "auto"},
  "tests": {"min_coverage": 85, "required_suites": ["unit"]},
  "security": {"osv_gate": "high", "sast_paths": ["src/**"]},
  "reproducibility": {"lockfiles_required": ["requirements.txt"], "pinned_python": "3.11.9"},
  "provenance": {"sign_proof_journal": True, "artifact_retention_days": 180},
  "custom_obligations": [],
}

SCHEMA_PATH = Path(".pec/ambition.schema.json")
AMBITION_PATH = Path(".pec/ambition.json")
OBLIGATIONS_LOCK_PATH = Path(".pec/obligations.lock")
PROOF_DELTA_PATH = Path(".pec/proof_delta.md")

ambition_app = typer.Typer()


def load_schema() -> Dict[str, Any]:
  with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    return json.load(f)


def ensure_pec_dir() -> None:
  Path(".pec").mkdir(parents=True, exist_ok=True)


def ask_list(prompt: str, default: List[str]) -> List[str]:
  raw = typer.prompt(f"{prompt} (séparé par des virgules)", ",".join(default))
  values = [v.strip() for v in raw.split(",") if v.strip()]
  return values


@ambition_app.command("init")
def cmd_init() -> None:
  """Assistant interactif (offline) pour créer .pec/ambition.json"""
  ensure_pec_dir()

  identity = typer.prompt("Identity (slug projet)", default="my-project")
  owners = ask_list("Owners (@gh ou email)", DEFAULTS["owners"])

  policy = typer.prompt("API stability policy (semver|frozen|internal)", DEFAULTS["api_stability"]["policy"])  # type: ignore[index]
  surface_paths = ask_list("API surface_paths (glob)", DEFAULTS["api_stability"]["surface_paths"])  # type: ignore[index]
  require_depr = typer.confirm("Require deprecation cycle?", DEFAULTS["api_stability"]["require_deprecation_cycle"])  # type: ignore[index]

  compliance_targets = ask_list(
    "Compliance targets (NIST-SSDF|SOC2|EU-AI-Act)",
    [],
  )

  changelog_path = typer.prompt("Changelog path", DEFAULTS["changelog"]["path"])  # type: ignore[index]
  changelog_required_for = ask_list(
    "Changelog required_for (minor|major|breaking)",
    DEFAULTS["changelog"]["required_for"],  # type: ignore[index]
  )

  versioning_file = typer.prompt("Versioning file (pyproject.toml|package.json|custom)", DEFAULTS["versioning"]["file"])  # type: ignore[index]
  bump_rules = typer.prompt("Version bump rules (auto|manual)", DEFAULTS["versioning"]["bump_rules"])  # type: ignore[index]

  min_cov = int(typer.prompt("Min coverage (0-100)", str(DEFAULTS["tests"]["min_coverage"]) ))  # type: ignore[index]
  suites = ask_list("Required test suites (unit|integration)", DEFAULTS["tests"]["required_suites"])  # type: ignore[index]

  osv_gate = typer.prompt("OSV gate (none|low|moderate|high|critical)", DEFAULTS["security"]["osv_gate"])  # type: ignore[index]
  sast_paths = ask_list("SAST paths (glob)", DEFAULTS["security"]["sast_paths"])  # type: ignore[index]

  lockfiles_required = ask_list("Lockfiles required", DEFAULTS["reproducibility"]["lockfiles_required"])  # type: ignore[index]
  pinned_python = typer.prompt("Pinned Python (ex 3.11.9 ou vide)", DEFAULTS["reproducibility"]["pinned_python"])  # type: ignore[index]
  pinned_python = pinned_python if pinned_python else None

  sign_proof = typer.confirm("Sign proof journal?", DEFAULTS["provenance"]["sign_proof_journal"])  # type: ignore[index]
  retention = int(typer.prompt("Artifact retention days", str(DEFAULTS["provenance"]["artifact_retention_days"]) ))  # type: ignore[index]

  ambition: Dict[str, Any] = {
    "identity": identity,
    "owners": owners,
    "compliance_targets": compliance_targets,
    "api_stability": {
      "policy": policy,
      "surface_paths": surface_paths,
      "require_deprecation_cycle": require_depr,
    },
    "changelog": {"path": changelog_path, "required_for": changelog_required_for},
    "versioning": {"file": versioning_file, "bump_rules": bump_rules},
    "tests": {"min_coverage": min_cov, "required_suites": suites},
    "security": {"osv_gate": osv_gate, "sast_paths": sast_paths},
    "reproducibility": {"lockfiles_required": lockfiles_required, "pinned_python": pinned_python},
    "provenance": {"sign_proof_journal": sign_proof, "artifact_retention_days": retention},
    "custom_obligations": [],
  }

  with AMBITION_PATH.open("w", encoding="utf-8") as f:
    json.dump(ambition, f, indent=2, ensure_ascii=False)
  print(f"[green]Écrit {AMBITION_PATH}[/green]")


@ambition_app.command("validate")
def cmd_validate() -> None:
  """Valide .pec/ambition.json via jsonschema + règles gaps."""
  ensure_pec_dir()
  if not AMBITION_PATH.exists():
    raise typer.Exit(code=2)

  ambition = json.loads(AMBITION_PATH.read_text(encoding="utf-8"))
  schema = load_schema()

  errors: List[str] = []
  validator = Draft202012Validator(schema)
  for err in sorted(validator.iter_errors(ambition), key=lambda e: e.path):
    loc = "/".join([str(x) for x in err.path])
    errors.append(f"schema:{loc}: {err.message}")

  gaps, recs = apply_gap_rules(ambition)
  for g in gaps:
    errors.append(f"gap:{g}")

  if errors:
    print("[red]Validation échouée:[/red]")
    for e in errors:
      print(f" - {e}")
    if recs:
      print("\n[bold]Recommandations:[/bold]")
      for r in recs:
        print(f" - {r}")
    raise typer.Exit(code=1)

  print("[green]OK: ambition.json valide[/green]")


@ambition_app.command("compile")
def cmd_compile() -> None:
  """Compile ambition → obligations.lock + proof_delta.md (déterministe)."""
  ensure_pec_dir()
  if not AMBITION_PATH.exists():
    raise typer.Exit(code=2)

  ambition = json.loads(AMBITION_PATH.read_text(encoding="utf-8"))
  obligations = compile_obligations(ambition)

  with OBLIGATIONS_LOCK_PATH.open("w", encoding="utf-8") as f:
    json.dump(obligations, f, indent=2, ensure_ascii=False)

  proof_delta = render_proof_delta(ambition, obligations)
  PROOF_DELTA_PATH.write_text(proof_delta, encoding="utf-8")

  print(f"[green]Écrit {OBLIGATIONS_LOCK_PATH} et {PROOF_DELTA_PATH}[/green]")


# --- Règles gaps ---

def apply_gap_rules(ambition: Dict[str, Any]) -> Tuple[List[str], List[str]]:
  gaps: List[str] = []
  recs: List[str] = []

  api = ambition.get("api_stability", {})
  if api.get("policy") == "semver":
    if not ambition.get("versioning", {}).get("file"):
      gaps.append("versioning.file requis pour policy=semver")
    if not ambition.get("changelog", {}).get("path"):
      gaps.append("changelog.path requis pour policy=semver")

  comp = ambition.get("compliance_targets", [])
  prov = ambition.get("provenance", {})
  if "SOC2" in comp:
    if prov.get("artifact_retention_days", 0) < 90:
      gaps.append("artifact_retention_days >= 90 requis pour SOC2")
    if prov.get("sign_proof_journal") is not True:
      recs.append("Activer provenance.sign_proof_journal pour SOC2")

  sec = ambition.get("security", {})
  gate = sec.get("osv_gate")
  if gate in ("high", "critical"):
    if not ambition.get("reproducibility", {}).get("lockfiles_required"):
      gaps.append("lockfiles_required non vide requis pour osv_gate >= high")
    if not ambition.get("reproducibility", {}).get("pinned_python"):
      recs.append("Recommander reproducibility.pinned_python pour osv_gate élevé")

  tests = ambition.get("tests", {})
  if isinstance(tests.get("min_coverage"), int) and tests.get("min_coverage", 0) >= 80:
    suites = tests.get("required_suites", [])
    if "unit" not in suites:
      gaps.append("tests.required_suites doit contenir 'unit' si min_coverage >= 80")

  owners = ambition.get("owners", [])
  if not owners or len(owners) < 1:
    gaps.append("au moins un owner requis")

  return gaps, recs


# --- Compilation obligations ---

def compile_obligations(ambition: Dict[str, Any]) -> List[Dict[str, Any]]:
  obligations: List[Dict[str, Any]] = []

  api = ambition.get("api_stability", {})
  if api.get("policy") == "semver":
    obligations.append({
      "id": "OBL-API-BREAK",
      "severity": "error",
      "when": "breaking_api_change",
      "action": "require_major_bump",
    })
    obligations.append({
      "id": "OBL-CHANGELOG",
      "severity": "error",
      "when": "public_change",
      "action": "require_changelog_entry",
      "path": ambition.get("changelog", {}).get("path"),
    })
    if api.get("require_deprecation_cycle"):
      obligations.append({
        "id": "OBL-DEPRECATION",
        "severity": "warning",
        "when": "public_change",
        "action": "require_deprecation_cycle",
      })

  tests = ambition.get("tests", {})
  if isinstance(tests.get("min_coverage"), int):
    obligations.append({
      "id": "OBL-COVERAGE-THRESHOLD",
      "severity": "error",
      "threshold": tests.get("min_coverage"),
      "suites": tests.get("required_suites", []),
    })

  sec = ambition.get("security", {})
  if sec.get("osv_gate") and sec.get("osv_gate") != "none":
    obligations.append({
      "id": "OBL-OSV-GATE",
      "severity": "error",
      "threshold": sec.get("osv_gate"),
      "scope": "modified_paths",
      "paths": sec.get("sast_paths", []),
    })

  repro = ambition.get("reproducibility", {})
  if repro.get("lockfiles_required"):
    obligations.append({
      "id": "OBL-LOCKFILES-PRESENT",
      "severity": "error",
      "files": repro.get("lockfiles_required"),
    })
    obligations.append({
      "id": "OBL-HASHED-BUILD",
      "severity": "warning",
      "action": "hash_build_inputs",
    })

  prov = ambition.get("provenance", {})
  if prov.get("sign_proof_journal"):
    obligations.append({
      "id": "OBL-PROOF-SIGN",
      "severity": "error",
      "action": "sign_proof_journal",
      "retention_days": prov.get("artifact_retention_days"),
    })

  for custom in ambition.get("custom_obligations", []) or []:
    obligations.append(custom)

  return obligations


def render_proof_delta(ambition: Dict[str, Any], obligations: List[Dict[str, Any]]) -> str:
  lines: List[str] = []
  api = ambition.get("api_stability", {})
  lines.append(
    f"API stability: {api.get('policy')} on {', '.join(api.get('surface_paths', []))} (deprecation cycle: {'yes' if api.get('require_deprecation_cycle') else 'no'})"
  )

  versioning = ambition.get("versioning", {})
  lines.append(f"Version bump: {versioning.get('bump_rules')} via {versioning.get('file')}")

  ch = ambition.get("changelog", {})
  lines.append(
    f"Changelog required for: {', '.join(ch.get('required_for', []))} → {ch.get('path')}"
  )

  tests = ambition.get("tests", {})
  lines.append(
    f"Coverage threshold: {tests.get('min_coverage')}% (suites: {', '.join(tests.get('required_suites', []))})"
  )

  sec = ambition.get("security", {})
  lines.append(
    f"Security gate: OSV ≥ {sec.get('osv_gate')} on {', '.join(sec.get('sast_paths', []))}"
  )

  repro = ambition.get("reproducibility", {})
  py = repro.get("pinned_python") or "unpin"
  lines.append(
    f"Reproducibility: {', '.join(repro.get('lockfiles_required', []))}, Python {py}"
  )

  prov = ambition.get("provenance", {})
  lines.append(
    f"Provenance: {'signed proof journal' if prov.get('sign_proof_journal') else 'unsigned'}, retain {prov.get('artifact_retention_days')} days"
  )

  lines.append(f"{len(obligations)} obligations activées")

  return "\n".join(lines) + "\n"
