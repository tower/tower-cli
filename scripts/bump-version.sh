#!/bin/bash

# Function to increment version
bump_version() {
    local version=$1
    local type=$2
    
    # Split version into major, minor, patch
    IFS='.' read -r major minor patch <<< "$version"
    
    case $type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            echo "Invalid bump type. Use major, minor, or patch"
            exit 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <major|minor|patch>"
    exit 1
fi

# Get current version from Cargo.toml workspace package section
current_version=$(grep '^version = ' Cargo.toml | head -1 | cut -d '"' -f 2)

if [ -z "$current_version" ]; then
    echo "Could not find version in Cargo.toml workspace.package section"
    exit 1
fi

# Calculate new version
new_version=$(bump_version "$current_version" "$1")

echo "Bumping version from $current_version to $new_version"

# Update version in Cargo.toml
if [ "$(uname)" == "Darwin" ]; then
    # macOS sed
    sed -i '' "s/^version = \"$current_version\"/version = \"$new_version\"/" Cargo.toml
else
    # GNU sed
    sed -i "s/^version = \"$current_version\"/version = \"$new_version\"/" Cargo.toml
fi

# Update version in pyproject.toml
if [ "$(uname)" == "Darwin" ]; then
    # macOS sed
    sed -i '' "s/^version = \"$current_version\"/version = \"$new_version\"/" pyproject.toml
else
    # GNU sed
    sed -i "s/^version = \"$current_version\"/version = \"$new_version\"/" pyproject.toml
fi

echo "Version bumped successfully in Cargo.toml and pyproject.toml!"

cargo build

# Do git things
git add Cargo.lock Cargo.toml pyproject.toml
git commit -m "Version bump to ${new_version}"
git tag "${new_version}"
