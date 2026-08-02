#!/bin/bash
set -e

POOL="${POOL:-"$(ls -1 / | grep pool | head -n1)"}"
YEAR="${YEAR:-$(date +%Y)}"
ARCHIVE_DIR="${BITBUCKET_ARCHIVE_DIR:-"/$POOL/archive/${YEAR}/Bitbucket"}"

REPO_URL="${REPO_URL:-"$1"}"
REPO_URL="${REPO_URL#/}"
REPO_URL="${REPO_URL#.git}"

# Extract workspace and repo from URL: https://bitbucket.org/{workspace}/{repo}
WORKSPACE=$(echo "$REPO_URL" | cut -d'/' -f4)
REPO_SLUG=$(echo "$REPO_URL" | cut -d'/' -f5)

if [[ -z "${WORKSPACE}" ]] || [[ -z "${REPO_SLUG}" ]] ; then
  echo 'no repo url or invalid repo url specified'
  exit 1
fi

# Assuming we are running from the project root. Adjust if necessary.
python3 bitbucket/archive_bitbucket_single.sh https://bitbucket.org/workspace/repo
