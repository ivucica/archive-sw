#!/bin/bash

# NOT TESTED
#
# pip install mitmproxy
# this includes mitmdump

# this is silly. can't we use a normal proxy and have mitmproxy / mitmdump just decode the traffic?

# --- 1. Configuration ---
PROXY_PORT=8080
# This is the file that will act as our cache
CACHE_FILE="github-api.mitm.flows"
# mitmproxy's default CA certificate path
CA_CERT_PATH="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"

# Dependency check
if ! command -v mitmdump >/dev/null || ! command -v jq >/dev/null; then
  echo "Error: Please install 'mitmproxy' and 'jq' to run this script." >&2
  echo "Try: pip install mitmproxy" >&2
  exit 1
fi

# --- 2. Setup Proxy & Cleanup ---

# This 'trap' command ensures that when the script exits
# (for any reason), it will kill the proxy process.
trap ' {
  echo -e "\nShutting down proxy (PID $MITM_PID)..."
  kill $MITM_PID
  wait $MITM_PID 2>/dev/null
  echo "Done."
} ' EXIT

MITM_CMD=""
if [ -f "$CACHE_FILE" ]; then
  # CACHE HIT: Cache file exists. Start in REPLAY mode.
  echo "Cache file found. Starting proxy in REPLAY mode." >&2
  MITM_CMD="mitmdump -p $PROXY_PORT -r $CACHE_FILE --server-replay --quiet --no-showhost"
else
  # CACHE MISS: No cache file. Start in RECORD mode.
  echo "No cache file. Starting proxy in RECORD mode. (Will create $CACHE_FILE)" >&2
  MITM_CMD="mitmdump -p $PROXY_PORT -w $CACHE_FILE --quiet --no-showhost"
fi

# Start the mitmdump proxy in the background
$MITM_CMD &
MITM_PID=$!

echo "Proxy started (PID $MITM_PID). Waiting for it to initialize..." >&2
sleep 2 # Give it a moment to start and generate the CA if this is the first run

# Check if the CA file exists after starting
if [ ! -f "$CA_CERT_PATH" ]; then
  echo "Error: mitmproxy CA not found at $CA_CERT_PATH" >&2
  echo "Try running 'mitmdump' once manually to generate it." >&2
  exit 1
fi

echo "Proxy ready. Beginning fetch..." >&2

# --- 3. Run the Pagination Script ---

# Set the initial URL
url="https://api.github.com/users/github/repos?per_page=100"

# Define the curl options to use the proxy and trust our CA
# This is the "injection" you asked for.
CURL_OPTS=(
  -s -i -L
  --proxy "http://localhost:$PROXY_PORT"
  --cacert "$CA_CERT_PATH"
)

while [ -n "$url" ]; do
  echo "Fetching $url (via proxy)" >&2
  
  # Run the original curl command with our new options
  response=$(curl "${CURL_OPTS[@]}" \
    -H "Accept: application/vnd.github.v3+json" \
    "$url")

  # Split headers and body
  headers=$(echo "$response" | sed -n '1,/^\r$/p' | head -n -1)
  body=$(echo "$response" | sed -n '/^\r$/,$p' | tail -n +2)

  # Process the body with jq
  echo "$body" | jq -r '.[].name'
  
  # Parse the 'next' link from the headers
  url=$(echo "$headers" | grep -i '^Link:' | \
        sed -n 's#.*<https://api.github.com\([^>]*\)>; rel="next".*#https://api.github.com\1#p' | \
        tr -d '\r')

done
