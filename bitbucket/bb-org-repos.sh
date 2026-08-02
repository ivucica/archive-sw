#!/bin/bash
ORG="${1:-$LOGNAME}"
set -e

cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
python3 "archive_bitbucket.py" --org "$ORG" "$@"
