#!/bin/bash
# S0-fast pre-commit hook

if [ "$1" == "install" ]; then
    cp -f "$0" .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "Hook installed to .git/hooks/pre-commit"
    exit 0
fi

echo "Running S0-fast pre-commit checks..."

# Fast linting on staged python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM -- "*.py")

if [ -z "$STAGED_FILES" ]; then
    echo "No Python files staged. Skipping."
    exit 0
fi

echo "Running ruff linter..."
ruff check --select I,E,F,W,B $STAGED_FILES -q

if [ $? -ne 0 ]; then
    echo "Ruff checks failed."
    exit 1
fi

echo "Running dmypy type-checker..."
dmypy run -- $STAGED_FILES

if [ $? -ne 0 ]; then
    echo "dmypy checks failed."
    exit 1
fi

echo "S0-fast checks passed."
exit 0