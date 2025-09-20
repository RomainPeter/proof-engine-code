import os
import subprocess
import sys


def main():
    journal = os.environ.get("PROOF_JOURNAL", ".proof/journal.ndjson")
    merkle = os.environ.get("PROOF_MERKLE", ".proof/merkle.json")
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
