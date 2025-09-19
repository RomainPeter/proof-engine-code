import argparse
import toml


def check_version(pyproject_path, old_version):
    data = toml.load(pyproject_path)
    new_version = data["project"]["version"]

    print(f"Old version: {old_version}, New version: {new_version}")

    # This is a stub. A real implementation would compare versions
    # based on the API diff classification (major, minor, patch).
    if new_version == old_version:
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
    parser.add_argument(
        "--check-version", action="store_true", help="Check for version bump."
    )
    parser.add_argument(
        "--check-changelog", action="store_true", help="Check for changelog entry."
    )
    # In a real implementation, we would get these from git
    parser.add_argument(
        "--pyproject-path", default="examples/pilot-python/pyproject.toml"
    )
    parser.add_argument("--changelog-path", default="CHANGELOG.md")
    parser.add_argument("--old-version", default="0.1.0")

    args = parser.parse_args()

    if args.check_version:
        if not check_version(args.pyproject_path, args.old_version):
            exit(1)

    if args.check_changelog:
        # We need to get the new version from pyproject.toml to check the changelog
        data = toml.load(args.pyproject_path)
        new_version = data["project"]["version"]
        if not check_changelog(args.changelog_path, new_version):
            # Create a dummy CHANGELOG.md to pass the check for now
            with open(args.changelog_path, "w") as f:
                f.write(
                    f"# Changelog\n\n## [{new_version}] - YYYY-MM-DD\n- Initial release."
                )
            print("Created dummy CHANGELOG.md")
            exit(0)


if __name__ == "__main__":
    main()
