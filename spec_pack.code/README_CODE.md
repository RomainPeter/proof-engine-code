# Proof Engine for Code (PEC)

This directory contains the specification and tooling for the Proof Engine for Code.

## Quickstart

1.  **Setup Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

2.  **Install Dependencies:**
    Make sure you have `pip-tools` installed (`pip install pip-tools`).
    Compile and install the locked dependencies.
    ```bash
    pip-compile spec_pack/requirements.txt --generate-hashes -o spec_pack/requirements.lock.txt
    pip install --no-deps --require-hashes -r spec_pack/requirements.lock.txt
    ```

3.  **Install Hooks:**
    ```bash
    # For Bash/Zsh
    ./scripts/hooks/pre-commit-code.sh install

    # For PowerShell
    ./scripts/hooks/pre-commit-code.ps1 install
    ```

4.  **Usage:**
    -   Modify a file in `src/`.
    -   `git add <modified_file>`
    -   `git commit -m "Your message"`
    -   The pre-commit hook will run the `S0-fast` checks.
    -   On `git push`, the `S1-quick` checks will run.
    -   The full suite runs in CI.
    -   Check the `.proof/` directory for generated evidence and the proof journal.
