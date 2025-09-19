import argparse
import subprocess
import json
import yaml
import sys
import os
from git import Repo

def get_diff_details(repo_path, commit_ref):
    repo = Repo(repo_path)
    if not repo.commit(commit_ref).parents:
        return {item.a_path: "added" for item in repo.index.diff(None)}
    parent = repo.commit(commit_ref).parents[0]
    diffs = parent.diff(commit_ref, create_patch=True)
    
    details = {}
    for diff in diffs:
        is_interface_change = False
        diff_text = diff.diff.decode('utf-8', errors='ignore')
        for line in diff_text.splitlines():
            if (line.startswith('+') or line.startswith('-')) and 'def ' in line:
                is_interface_change = True
                break
        
        if is_interface_change:
            details[diff.a_path] = "interface"
        elif diff.a_path.endswith((".py")):
            details[diff.a_path] = "behavior"
        elif "requirements" in diff.a_path or "pyproject.toml" in diff.a_path:
            details[diff.a_path] = "deps"
        else:
            details[diff.a_path] = "trivial"
            
    return details

def run_verifiers(obligations_to_run, all_obligations, all_verifiers):
    print(f"\n--- Running {len(obligations_to_run)} verifiers ---")
    obligation_map = {ob['id']: ob for ob in all_obligations}
    
    for ob_id in obligations_to_run:
        if ob_id not in obligation_map: continue
        verifier_id = obligation_map[ob_id]['verifier']
        if verifier_id not in all_verifiers: continue

        command = all_verifiers[verifier_id]['cmd']
        print(f"\n[RUN] Obligation: {ob_id} | Verifier: {verifier_id}")
        print(f"$ {command}")
        
        my_env = os.environ.copy()
        if verifier_id == 'tests_coverage_targeted':
            example_path = os.path.abspath('examples/pilot-python')
            my_env['PYTHONPATH'] = f"{example_path}{os.pathsep}{my_env.get('PYTHONPATH', '')}"

        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, env=my_env)
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
    parser.add_argument("--diff", default="HEAD", help="Git commit ref to diff against its parent.")
    parser.add_argument("--check-api-diff", action="store_true", help="Run the API diff check stub.")
    args = parser.parse_args()

    if args.check_api_diff:
        print("Checking for API diffs... OK (stub)")
        sys.exit(0)

    with open("spec_pack.code/obligations_code.yaml", "r") as f: all_obligations = yaml.safe_load(f)
    with open("spec_pack.code/app/verifiers.yaml", "r") as f: all_verifiers = yaml.safe_load(f)

    changed_files_details = get_diff_details(".", args.diff)
    print(f"Found {len(changed_files_details)} changed files:")
    for f, c_type in changed_files_details.items(): print(f"- {f} (type: {c_type})")

    triggered_obligations = []
    for f, diff_class in changed_files_details.items():
        for ob in all_obligations:
            if diff_class in ob['when']:
                triggered_obligations.append(ob['id'])

    if any(ob['id'] == 'O-CODE-TRACE-1' for ob in all_obligations):
        triggered_obligations.append('O-CODE-TRACE-1')

    min_obligations = sorted(list(set(triggered_obligations)))
    
    print("--- Minimal obligations triggered ---")
    for ob in min_obligations: print(f"- {ob}")

    if not run_verifiers(min_obligations, all_obligations, all_verifiers):
        print("\n--- Verification failed ---")
        sys.exit(1)

    print("\n--- Verification successful ---")

if __name__ == "__main__":
    main()
