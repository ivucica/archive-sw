---
description: Archive any Git repository.
mode: subagent
prompt: Use the 'archive-any' skill to archive the provided repository URL.
permission:
  skill:
    "archive-any": allow
  bash:
    "./archive_sw.sh*": allow
---
## What I do
- Archives a single Git repository from any source (e.g., GitHub) by calling `./archive_sw.sh <url>`.

## When to use me
Use this when you need to quickly create an archive of a specific public or accessible repository.

## Usage Example
```bash
./archive_sw.sh https://github.com/owner/repo
```