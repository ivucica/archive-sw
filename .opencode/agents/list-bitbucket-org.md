---
description: List all repositories in a Bitbucket workspace (org or user).
mode: subagent
prompt: Use the 'list-bitbitbucket-org' skill to list the provided Bitbucket workspace (org or user).
permission:
  skill:
    "list-bitbucket-org": allow
  bash:
    "./bb-org-repos.sh*": allow
    "bitbucket/bb-org-repos.sh*": allow
---
## What I do
- Lists all repositories within a specified Bitbucket workspace by calling `bitbucket/bb-org-repos.sh <workspace>`.

## When to use me
Use this when you need to perform a listing of all repositories in an entire Bitbucket organization's (workspace) repositories.

## Usage Example
```bash
bitbucket/bb-org-repos.sh my-bitbucket-workspace
```