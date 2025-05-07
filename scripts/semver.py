#!/usr/bin/env python3
import os
import sys
import re
import argparse

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEMVER_EXP = re.compile("\d+\.\d+(\.\d+)?(-rc\.(\d+))?")

class Version:
    def __init__(self, version_str):
        version_str = version_str.removeprefix("v")

        if SEMVER_EXP.fullmatch(version_str):
            parts = version_str.split(".")

            self.major = int(parts[0])
            self.minor = int(parts[1])

            if len(parts) > 2:
                if "-rc" in parts[2]:
                    prerelease_parts = parts[2].split("-rc")
                    self.patch = int(prerelease_parts[0])
                else:
                    self.patch = int(parts[2])

                if len(parts) > 3:
                    self.prerelease = int(parts[3])
                else:
                    self.prerelease = 0
            else:
                self.patch = 0
                self.prerelease = 0
        else:
            self.major = 0
            self.minor = 0
            self.patch = 0
            self.prerelease = 0

    def is_valid(self):
        return self.minor >= 0

    def __eq__(self, other):
        if isinstance(other, Version):
            return self.major == other.major and self.minor == other.minor and self.patch == other.patch
        else:
            return False

    def to_tag_string(self):
        if self.prerelease > 0:
            return "{major}.{minor}.{patch}-rc.{prerelease}".format(major=self.major, minor=self.minor, patch=self.patch, prerelease=self.prerelease)
        else:
            return "{major}.{minor}.{patch}".format(major=self.major, minor=self.minor, patch=self.patch)

    def to_python_string(self):
        if self.prerelease > 0:
            return "{major}.{minor}.{patch}rc{prerelease}".format(major=self.major, minor=self.minor, patch=self.patch, prerelease=self.prerelease)
        else:
            return "{major}.{minor}.{patch}".format(major=self.major, minor=self.minor, patch=self.patch)

def get_all_versions():
    # Wait for this to complete.
    proc = os.popen("git fetch --tags")

    # we read from this to have it complete before we proceed.
    _ = proc.read()

    stream = os.popen("git --no-pager tag")
    tags = stream.read().split("\n")
    return [Version(tag) for tag in tags]

def get_version_set(version):
    all_versions = get_all_versions()
    return [v for v in all_versions if v.major == version.major and v.minor == version.minor]

def get_version_patch(version):
    return version.patch

def get_current_version(base):
    v = Version(base)
    versions = get_version_set(v)

    if len(versions) < 1:
        return None
    else:
        current_version = max(versions, key=get_version_patch)

        # find all the versions that are the same major, minor, and patch
        same_versions = [v for v in versions if v == current_version]

        # Now if there are prereleases, we want the one with a max prerelease number
        if len(same_versions) > 1:
            released_versions = [ver for ver in same_versions if ver.prerelease == 0]

            # If there is a released version, then let's go with this.
            if len(release_versions) > 1:
                return release_versions[0]
            else:
                return max(same_versions, key=lambda x: x.prerelease)
        else:
            return same_versions[0]

def get_version_base():
    path = os.path.join(BASE_PATH, "version.txt")

    with open(path) as file:
        line = file.readline().rstrip()
        return line

def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in {'true', 'yes', '1'}:
        return True
    elif value.lower() in {'false', 'no', '0'}:
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected (true/false).')

def replace_line_with_regex(file_path, pattern, replace_text):
    """
    Replace lines matching a regex pattern with replace_text in the specified file.
    
    Args:
        file_path (str): Path to the file to modify
        pattern (re.Pattern): Regex pattern to match lines
        replace_text (str): Text to replace the entire line with
    """
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Use regex to replace lines matching the pattern
    new_content = pattern.sub(replace_text + '\n', content)
    print(new_content)
    
    with open(file_path, 'w') as file:
        file.write(new_content)
    
    print(f"Regex replacement complete in {file_path}")

def update_cargo_file(version):
    pattern = re.compile(r'^\s*version\s*=\s*".*"$', re.MULTILINE)
    replace_line_with_regex("Cargo.toml", pattern, f'version = "{version.to_tag_string()}"')

def update_pyproject_file(version):
    pattern = re.compile(r'^\s*version\s*=\s*".*"$', re.MULTILINE)
    replace_line_with_regex("pyproject.toml", pattern, f'version = "{version.to_python_string()}"')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='semver',
        description='Manages the semantic versioning of the projects',
        epilog='This is the epilog'
    )

    parser.add_argument("-i", "--patch", type=str2bool, required=False, default=False, help="Increment the patch version")
    parser.add_argument("-p", "--prerelease", type=str2bool, required=False, default=False, help="Include the fact that this is a prerelease version")
    parser.add_argument("-w", "--write", type=str2bool, required=False, default=False, help="Update the various tools in this repository")
    args = parser.parse_args()

    version_base = get_version_base()

    if args.patch:
        version = get_current_version(version_base)

        if version is None:
            version = Version(version_base)
        else:
            version.patch += 1

    else:
        version = get_current_version(version_base)

    if args.prerelease:
        version.prerelease += 1

    if args.write:
        update_cargo_file(version)
        update_pyproject_file(version)

        # Do a cargo build to update the lock file
        os.system("cargo build")
        os.system("uv lock")
    else:
        print(version.to_tag_string(), end='', flush=True)
