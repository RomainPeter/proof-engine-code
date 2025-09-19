import argparse
import subprocess
import yaml
import sys
import os
from git import Repo
import libcst as cst


# --- Classification des changements ---
class TrivialChangeDetector(cst.CSTVisitor):
    def __init__(self):
        self.is_trivial = True

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.is_trivial = False


def get_diff_files(repo_path, commit_ref):
    repo = Repo(repo_path)
    if not repo.commit(commit_ref).parents:
        return [item.a_path for item in repo.index.diff(None) if item.a_path]
    parent = repo.commit(commit_ref).parents[0]
    diff = parent.diff(commit_ref)
    return [item.a_path for item in diff.iter_change_type("M")]


def classify_change(file_path):
    if "requirements" in file_path or "pyproject.toml" in file_path:
        return "deps"
    if not file_path.endswith(".py"):
        return "other"
    with open(file_path, "r") as f:
        source = f.read()
        if "def " in source:
            return "behavior"
    return "trivial"


# --- Moteur d'exécution ---
def run_verifiers(obligations_to_run, all_obligations, all_verifiers):
    print(f"\n--- Running {len(obligations_to_run)} verifiers ---")
    obligation_map = {ob["id"]: ob for ob in all_obligations}

    for ob_id in obligations_to_run:
        if ob_id not in obligation_map:
            continue

        verifier_id = obligation_map[ob_id]["verifier"]
        if verifier_id not in all_verifiers:
            continue

        command = all_verifiers[verifier_id]["cmd"]
        print(f"\n[RUN] Obligation: {ob_id} | Verifier: {verifier_id}")
        print(f"$ {command}")

        my_env = os.environ.copy()
        # FIX: Add example project to PYTHONPATH for test discovery
        if verifier_id == "tests_coverage_targeted":
            example_path = os.path.abspath("examples/pilot-python")
            current_python_path = my_env.get("PYTHONPATH", "")
            my_env["PYTHONPATH"] = f"{example_path}{os.pathsep}{current_python_path}"

        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                env=my_env,
            )
            print(result.stdout)
            print(f"[PASS] {ob_id}")
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            print(e.stderr)
            print(f"[FAIL] {ob_id}")
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Ambition to Compliance Engine (Code)")
    parser.add_argument(
        "--level", default="S1-quick", help="Verification level to run."
    )
    parser.add_argument(
        "--diff", default="HEAD", help="Git commit ref to diff against its parent."
    )
    args = parser.parse_args()

    with open("spec_pack.code/obligations_code.yaml", "r") as f:
        all_obligations = yaml.safe_load(f)
    with open("spec_pack.code/app/verifiers.yaml", "r") as f:
        all_verifiers = yaml.safe_load(f)

    repo_path = "."
    changed_files = get_diff_files(repo_path, args.diff)
    print(f"Found {len(changed_files)} changed files:")
    for f in changed_files:
        print(f"- {f}")

    triggered_obligations = []
    for f in changed_files:
        diff_class = classify_change(f)
        for ob in all_obligations:
            if diff_class in ob["when"]:
                triggered_obligations.append(ob["id"])

    if any(ob["id"] == "O-CODE-TRACE-1" for ob in all_obligations):
        triggered_obligations.append("O-CODE-TRACE-1")

    min_obligations = sorted(list(set(triggered_obligations)))

    print("\n--- Minimal obligations triggered ---")
    for ob in min_obligations:
        print(f"- {ob}")

    if not run_verifiers(min_obligations, all_obligations, all_verifiers):
        print("\n--- Verification failed ---")
        sys.exit(1)

    print("\n--- Verification successful ---")


if __name__ == "__main__":
    main()
