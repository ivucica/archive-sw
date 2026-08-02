#!/bin/bash
set -e

POOL="${POOL:-"$(ls -1 / | grep pool | head -n1)"}"
YEAR="${YEAR:-$(date +%Y)}"
ARCHIVE_DIR="${BITBUCKET_ARCHIVE_DIR:-"/$POOL/archive/${YEAR}/Software/bitbucket.org"}"

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

cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
python3 archive_bitbucket.py --org "$WORKSPACE" --repo "$REPO_SLUG" --archive_dir "$ARCHIVE_DIR" "$@"
