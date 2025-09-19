#!/bin/bash
# S1-quick pre-push hook

if [ "$1" == "install" ]; then
    cp -f "$0" .git/hooks/pre-push
    chmod +x .git/hooks/pre-push
    echo "Hook installed to .git/hooks/pre-push"
    exit 0
fi

echo "Running S1-quick pre-push checks..."

# Run targeted tests and other checks
python spec_pack.code/tools/a2c_code.py --level S1-quick --diff $(git rev-parse HEAD)

if [ $? -ne 0 ]; then
    echo "S1-quick pre-push checks failed."
    exit 1
fi

echo "S1-quick checks passed."
exit 0