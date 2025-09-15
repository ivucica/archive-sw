#!/bin/bash

USER="${1:-$LOGNAME}"
set -e

# Set the initial URL
# Replace 'github' with the desired user or organization
url="https://api.github.com/users/$USER/repos?per_page=100"

# 1. Check for the namespaced env var first.
# 2. If not set, check if 'aria2c' exists.
# 3. If not, default to 'curl'.
FETCHER=""
if [ -n "$PAGINATE_FETCHER" ]; then
  FETCHER="$PAGINATE_FETCHER"
  echo "Using fetcher: $FETCHER (from env var)" >&2
elif command -v aria2c >/dev/null 2>&1; then
  FETCHER="aria2c"
  echo "Using fetcher: aria2c (default, binary found)" >&2
else
  FETCHER="curl"
  echo "Using fetcher: curl (default, aria2c not found)" >&2
fi

# Loop until no more "next" Link header is found
while [ -n "$url" ]; do
  set -v
  echo "Fetching $url" >&2

  if [ "$FETCHER" = "aria2c" ]; then
    ## Use aria2c: one call, headers to temp file, body to var
    #header_file=$(mktemp)
    # We must use two commands:

    # 1. Use curl -I (HEAD request) just to get the headers
    headers=$(curl -s -I -L \
      -H "Accept: application/vnd.github.v3+json" \
      "$url")

    # 2. Use aria2c just to get the body (piped to stdout)
    # This allows us to use --disk-cache
    body=$(aria2c -q --disk-cache=16M \
      --header="Accept: application/vnd.github.v3+json" \
      -o - "$url" 2>/dev/null)

    # -q: quiet
    # --disk-cache: as requested
    # --follow-http=true: same as curl -L
    # --dump-header: saves headers to our temp file
    # -o -: outputs the body to stdout
    # 2>/dev/null: silences aria2c's own status messages
    #body=$(aria2c -q --disk-cache=16M --follow-http=true \
    #  --header="Accept: application/vnd.github.v3+json" \
    #  --dump-header="$header_file" \
    #  -o - "$url" 2>/dev/null)

    #headers=$(cat "$header_file")
    #rm "$header_file"

  else
    # Use curl (Original logic): one call, headers+body to var
    # Fetch the URL, including headers (-i) and following redirects (-L)
    # We use a temporary file to hold the full response (headers + body)
    response=$(curl -s -i -L \
      -H "Accept: application/vnd.github.v3+json" \
      "$url")

    ## Extract the body (everything after the first blank line)
    ## and pipe it to jq
    #body=$(echo "$response" | sed -n '/^\r$/,$p' | tail -n +2)

    # Split the single response into headers and body
    # Headers: from line 1 up to (but not including) the blank line
    headers=$(echo "$response" | sed -n '1,/^\r$/p' | head -n -1)
    # Body: everything after the blank line
    body=$(echo "$response" | sed -n '/^\r$/,$p' | tail -n +2)
  fi

  echo "$body" | jq -r '.[].name'

  # Extract the 'next' link from the headers
  # 1. grep for 'Link:' header
  # 2. Use sed to find the URL part with rel="next"
  # 3. Clean it up to get just the URL
  #url=$(echo "$response" | grep -i '^Link:' | \
  #      sed -n 's/.*<https://api.github.com\([^>]*\)>; rel="next".*/https:\/\/api.github.com\1/p')
  #url=$(echo "$response" | grep -i '^Link:' | \
  #      sed -n 's#.*<https://api.github.com\([^>]*\)>; rel="next".*#https://api.github.com\1#p')
  url=$(echo "$headers" | grep -i '^Link:' | \
        sed -n 's#.*<https://api.github.com\([^>]*\)>; rel="next".*#https://api.github.com\1#p')

done
