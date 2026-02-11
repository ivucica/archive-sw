#!/bin/bash

# Example:
# GHORG=something
# JOBS=3
# ~/zzz-gh-org-repos.sh $GHORG | REPO_UPDATE=1 parallel --joblog /tmp/${GHORG}_job_progress.log --resume --resume-failed -P${JOBS:-3} --bar -I{} ~/zzz-archive_sw.sh https://github.com/$GHORG/{}
# or
# curl https://api.github.com/users/$GHORG/repos?per_page=100 | jq -r '.[] | select(.disabled != true) | .name'   | REPO_UPDATE=1 parallel --joblog /tmp/${GHORG}_job_progress.log --resume --resume-failed -P${JOBS:-3} --bar -I{} ~/zzz-archive_sw.sh https://github.com/$GHORG/{}

set -e
POOL="${POOL:-"$(ls -1 / | grep pool | head -n1)"}"
YEAR="${YEAR:-$(date +%Y)}"
SW_ROOT="${SW_ROOT:-"/$POOL/archive/${YEAR}/Software"}"

REPO_URL="${REPO_URL:-"$1"}"
REPO_URL="${REPO_URL#/}"
REPO_URL="${REPO_URL#.git}"
REPO_PATH="${REPO_URL#https://}"  # TODO: support 'ssh://' or 'git@' style URLs, or even 'http://'

if [[ -z "${REPO_URL}" ]] || [[ -z "${REPO_PATH}" ]] ; then
  echo 'no repo url or invalid repo url specified'
  exit 1
fi

ORG_PATH="$(dirname "${REPO_PATH}")"
REPO_NAME="$(basename "${REPO_PATH}")"

set -v
mkdir -p "${SW_ROOT}"/"${ORG_PATH}"
cd "${SW_ROOT}"/"${ORG_PATH}"

echo "Into ${PWD}/${REPO_NAME}.git" >/dev/stderr

[[ -e "${REPO_NAME}.git" ]] && ( [[ ! -z "${REPO_UPDATE}" ]] && ( echo "Fetching ${REPO_URL} updates to ${PWD}..." >/dev/stderr ; cd "${REPO_NAME}.git" && git fetch ) ) || true
[[ -e "${REPO_NAME}.git" ]] || git clone --mirror "${REPO_URL}"
[[ -e "${REPO_NAME}" ]] && ( [[ ! -z "${REPO_UPDATE_WK}" ]] && ( echo "Applying updates for ${REPO_URL} to ${PWD}..." >/dev/stderr ; cd "${REPO_NAME}" && git fetch && git pull ) ) || true
[[ -e "${REPO_NAME}" ]] || git clone --reference "$(realpath "${REPO_NAME}.git")" "${REPO_URL}"
