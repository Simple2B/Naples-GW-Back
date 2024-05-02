#!/bin/bash

# Ensure that the user has provided a valid argument
case $1 in
    patch)
        ;;
    minor)
        ;;
    major)
        ;;
    *)
        echo "Invalid argument! Usage: $0 [patch|minor|major]"
        exit 1
        ;;
esac


# Ensure that the working directory is clean
if [[ $(git status -s) ]]
then
    echo "Working directory is not clean! Please commit all changes before running this script."
    exit 1
fi

# Ensure that the local branch is up to date with the remote branch
git pull

# Update the version in the pyproject.toml file
poetry version $1
new_version=$(poetry version -s)

# Commit the change
git commit -am v${new_version}

# Create an annotated Git tag with the updated version
git tag -a -m v${new_version} v${new_version}

git push --follow-tags

echo "Version increased to $new_version and Git tag <v${new_version}> created."
