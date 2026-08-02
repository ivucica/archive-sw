---
description: Archive all repositories in a GitHub organization.
mode: subagent
prompt: Use the 'archive-github-org' skill to archive the provided GitHub organization.
permission:
  skill:
    "archive-github-org": allow
  bash:
    "./archive_sw_ghorg.sh*": allow
---
## What I do
- Archives all repositories within a specified GitHub organization by calling `./archive_sw_ghorg.sh <org>`.

## When to use me
Use this when you need to perform a bulk archival of an entire GitHub organization's repositories.

## Usage Example
```bash
./archive_sw_ghorg.sh my-github-org
```