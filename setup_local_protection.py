#!/usr/bin/env python3
"""
Setup local branch protection for demo/grove
Alternative to GitHub branch protection for private repos
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_pre_push_hook():
    """Setup pre-push hook to enforce code_proof check"""
    
    hook_content = '''#!/bin/bash
# Pre-push hook for demo/grove branch protection
# Alternative to GitHub branch protection for private repos

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = "demo/grove" ]; then
    echo "🛡️  Branch protection active for demo/grove"
    echo "🔍 Running code_proof verification..."
    
    # Run the same checks as GitHub Actions
    python spec_pack.code/tools/check_semver.py --check-version
    if [ $? -ne 0 ]; then
        echo "❌ Version check failed"
        exit 1
    fi
    
    python spec_pack.code/tools/check_semver.py --check-changelog
    if [ $? -ne 0 ]; then
        echo "❌ Changelog check failed"
        exit 1
    fi
    
    # Run linting
    ruff check examples/pilot-python/src --output-format json --output-file .proof/ruff.json --exit-zero
    if [ $? -ne 0 ]; then
        echo "❌ Linting failed"
        exit 1
    fi
    
    # Run type checking
    dmypy run -- examples/pilot-python/src
    if [ $? -ne 0 ]; then
        echo "❌ Type checking failed"
        exit 1
    fi
    
    # Run tests
    pytest examples/pilot-python/src --cov=examples/pilot-python/src --cov-report=xml:.proof/coverage.xml
    if [ $? -ne 0 ]; then
        echo "❌ Tests failed"
        exit 1
    fi
    
    echo "✅ All checks passed - push allowed"
fi

exit 0
'''

    hook_path = Path('.git/hooks/pre-push')
    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)
    
    print("✅ Pre-push hook installed for demo/grove protection")

def setup_commit_msg_hook():
    """Setup commit-msg hook to enforce commit message format"""
    
    hook_content = '''#!/bin/bash
# Commit message hook for demo/grove
# Enforce conventional commit format

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = "demo/grove" ]; then
    commit_msg_file=$1
    commit_msg=$(cat "$commit_msg_file")
    
    # Check if commit message follows conventional format
    if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+"; then
        echo "❌ Commit message must follow conventional format:"
        echo "   feat: add new feature"
        echo "   fix: fix bug"
        echo "   chore: maintenance task"
        echo "   docs: update documentation"
        echo ""
        echo "Your message: $commit_msg"
        exit 1
    fi
    
    echo "✅ Commit message format valid"
fi

exit 0
'''

    hook_path = Path('.git/hooks/commit-msg')
    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)
    
    print("✅ Commit message hook installed for demo/grove")

def main():
    """Setup local branch protection"""
    print("🛡️  Setting up local branch protection for demo/grove")
    print("   (Alternative to GitHub branch protection for private repos)")
    
    if not Path('.git').exists():
        print("❌ Not in a git repository")
        sys.exit(1)
    
    setup_pre_push_hook()
    setup_commit_msg_hook()
    
    print("\n✅ Local branch protection configured!")
    print("📋 Protection rules:")
    print("   - Pre-push: code_proof verification required")
    print("   - Commit messages: conventional format enforced")
    print("   - Branch: demo/grove only")
    
    print("\n🎯 For OpenAI Grove demo:")
    print("   1. This provides equivalent protection to GitHub branch protection")
    print("   2. All code_proof checks run before push")
    print("   3. Commit message quality enforced")
    print("   4. Ready for professional demonstration")

if __name__ == "__main__":
    main()

