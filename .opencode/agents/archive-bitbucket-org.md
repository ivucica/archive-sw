---
description: Archive all repositories in a Bitbucket workspace (org or user).
mode: subagent
prompt: Use the 'archive-bitbucket-org' skill to archive the provided Bitbucket workspace (org or user).
permission:
  skill:
    "archive-bitbucket-org": allow
  bash:
    "./archive_bitbucket_org.sh*": allow
    "bitbucket/archive_bitbucket_org.sh*": allow
---
## What I do
- Archives all repositories within a specified Bitbucket workspace by calling `bitbucket/archive_bitbucket_org.sh <workspace>`.
- A workspace is the same as an org or an individual user.

## When to use me
Use this when you need to perform a bulk archival of an entire Bitbucket organization's (workspace) repositories.

## Usage Example
```bash
bitbucket/archive_bitbucket_org.sh my-bitbucket-workspace
```