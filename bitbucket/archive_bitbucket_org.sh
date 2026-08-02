#!/bin/bash
set -e

WORKSPACE=${1:?must pass bitbucket workspace name}
JOBS=${JOBS:-${2:-3}}

SCR="$(realpath "${0}")"
SCRDIR="$(dirname "${SCR}")"
JOBPROGLOG=/tmp/"${WORKSPACE}"_job_progress.log

echo "*** Progress logged in ${JOBPROGLOG} (remove if you want to restart from scratch)"

cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
python3 archive_bitbucket.py --org="$WORKSPACE" --list | parallel --joblog "${JOBPROGLOG}" --resume --resume-failed -P"${JOBS:?}" --bar -I{} "${SCRDIR}/archive_bitbucket_single.sh" https://bitbucket.org/"${WORKSPACE}"/{}
