import argparse
import toml
import subprocess
import sys

def get_parent_file_content(path):
    try:
        content = subprocess.check_output(["git", "show", f"HEAD~1:{path}"], text=True, stderr=subprocess.DEVNULL)
        return content
    except subprocess.CalledProcessError:
        return None # File might not have existed in parent

def check_version(pyproject_path):
    current_data = toml.load(pyproject_path)
    current_version = current_data["project"]["version"]

    parent_content = get_parent_file_content(pyproject_path)
    if parent_content is None:
        print("Success: pyproject.toml is new, version bump is implicit.")
        return True

    parent_data = toml.loads(parent_content)
    parent_version = parent_data["project"]["version"]

    print(f"Old version: {parent_version}, New version: {current_version}")
    if current_version == parent_version:
        print("Error: Version has not been bumped.")
        return False
    
    print("Success: Version has been bumped.")
    return True

def check_changelog(changelog_path, version):
    with open(changelog_path, "r") as f:
        content = f.read()
    
    if f"## [{version}]" not in content:
        print(f"Error: Changelog entry for version {version} not found.")
        return False

    print(f"Success: Changelog entry for {version} found.")
    return True

def main():
    parser = argparse.ArgumentParser(description="SemVer and Changelog Checker")
    parser.add_argument("--check-version", action="store_true")
    parser.add_argument("--check-changelog", action="store_true")
    parser.add_argument("--pyproject-path", default="examples/pilot-python/pyproject.toml")
    parser.add_argument("--changelog-path", default="CHANGELOG.md")
    args = parser.parse_args()

    if args.check_version:
        if not check_version(args.pyproject_path):
            sys.exit(1)
            
    if args.check_changelog:
        data = toml.load(args.pyproject_path)
        new_version = data["project"]["version"]
        if not check_changelog(args.changelog_path, new_version):
            sys.exit(1)

if __name__ == "__main__":
    main()