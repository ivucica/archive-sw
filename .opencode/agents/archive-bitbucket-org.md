---
description: Archive all repositories in a Bitbucket workspace.
mode: subagent
prompt: Use the 'archive-bitbucket-org' skill to archive the provided Bitbucket workspace.
permission:
  skill:
    "archive-bitbucket-org": allow
  bash:
    "./archive_bitbucket_org.sh*": allow
---
## What I do
- Archives all repositories within a specified Bitbucket workspace by calling `./archive_bitbucket_org.sh <workspace>`.

## When to use me
Use this when you need to perform a bulk archival of an entire Bitbucket organization's (workspace) repositories.

## Usage Example
```bash
./archive_bitbucket_org.sh my-bitbucket-workspace
```