#!/bin/bash
set -e

REPO_URL="${REPO_URL:-"$1"}"
REPO_URL="${REPO_URL#/}"
REPO_URL="${REPO_URL#.git}"

# Extract workspace and repo from URL: https://bitbucket.org/{workspace}/{repo}
WORKSPACE=$(echo "$REPO_URL" | cut -d'/' -f4)
REPO_SLUG=$(echo "$REPO_URL" | cut -d'/' -f5)

if [[ -z "${WORKSPACE}" ]] || [[ -z "${REPO_SLUG}" ]]; then
  echo 'no repo url or invalid repo url specified'
  exit 1
fi

# Assuming we are running from the project root. Adjust if necessary.
python3 bitbucket/archive_bitbucket.py --org="$WORKSPACE" --repo="$REPO_SLUG"
