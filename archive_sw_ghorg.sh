#!/bin/bash

# Also used by child script:
# REPO_UPDATE=1 - update mirror if it already exists
# REPO_UPDATE_WK=1 - update working copy too (from mirror)
GHORG=${1:?must pass github org name}
JOBS=${JOBS:-${2:-3}}

SCR="$(realpath "${0}")"
SCRDIR="$(dirname "${SCR}")"
JOBPROGLOG=/tmp/"${GHORG}"_job_progress.log

echo "*** Progress logged in ${JOBPROGLOG} (remove if you want to restart from scratch)"

"${SCRDIR}"/gh-org-repos.sh "${GHORG}" | parallel --joblog "${JOBPROGLOG}" --resume --resume-failed -P"${JOBS:?}" --bar -I{} "${SCRDIR}"/archive_sw.sh https://github.com/$GHORG/{}
