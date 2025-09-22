#!/usr/bin/env python3
"""
Setup script for proof-engine-code public repository
Automates the creation and configuration of the public repository
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def setup_git_remote():
    """Setup git remote for the public repository"""
    print("🚀 Setting up public repository...")
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        print("❌ Not in a git repository")
        return False
    
    # Add remote origin
    remote_url = "https://github.com/RomainPeter/proof-engine-code.git"
    
    # Check if remote already exists
    result = run_command("git remote -v", "Checking existing remotes")
    if remote_url in result:
        print("✅ Remote already configured")
    else:
        run_command(f"git remote add origin {remote_url}", "Adding remote origin")
    
    return True

def push_to_github():
    """Push code and tags to GitHub"""
    print("📤 Pushing to GitHub...")
    
    # Push main branch
    if run_command("git push -u origin main", "Pushing main branch"):
        print("✅ Main branch pushed")
    else:
        print("❌ Failed to push main branch")
        return False
    
    # Push tags
    if run_command("git push --tags", "Pushing tags"):
        print("✅ Tags pushed")
    else:
        print("❌ Failed to push tags")
        return False
    
    return True

def verify_setup():
    """Verify the repository setup"""
    print("🔍 Verifying setup...")
    
    # Check git status
    result = run_command("git status", "Checking git status")
    if "nothing to commit, working tree clean" in result:
        print("✅ Working tree clean")
    else:
        print("⚠️ Working tree not clean")
    
    # Check remotes
    result = run_command("git remote -v", "Checking remotes")
    if "proof-engine-code" in result:
        print("✅ Remote configured")
    else:
        print("❌ Remote not configured")
    
    # Check tags
    result = run_command("git tag", "Checking tags")
    if "v0.1.1-mirror" in result:
        print("✅ Tag v0.1.1-mirror found")
    else:
        print("❌ Tag v0.1.1-mirror not found")
    
    return True

def main():
    """Main setup function"""
    print("🔒 Proof Engine for Code - Public Repository Setup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path('action.yml').exists():
        print("❌ action.yml not found. Are you in the proof-engine-code directory?")
        sys.exit(1)
    
    # Setup git remote
    if not setup_git_remote():
        print("❌ Failed to setup git remote")
        sys.exit(1)
    
    # Verify setup
    if not verify_setup():
        print("❌ Setup verification failed")
        sys.exit(1)
    
    print("\n🎯 Next steps:")
    print("1. Create the repository on GitHub: https://github.com/new")
    print("   - Name: proof-engine-code")
    print("   - Description: Minimal proof engine for code changes (open-core)")
    print("   - Visibility: Public")
    print("   - Don't initialize (we have code)")
    print("")
    print("2. Run this script again to push the code:")
    print("   python setup_public_repo.py --push")
    print("")
    print("3. Configure branch protection via GitHub UI")
    print("4. Test the workflows by creating a PR")
    
    # If --push flag is provided, push to GitHub
    if "--push" in sys.argv:
        print("\n🚀 Pushing to GitHub...")
        if push_to_github():
            print("\n✅ Repository setup complete!")
            print("🔗 Repository: https://github.com/RomainPeter/proof-engine-code")
        else:
            print("\n❌ Failed to push to GitHub")
            sys.exit(1)

if __name__ == "__main__":
    main()



