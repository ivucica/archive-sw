---
description: Archive a single Bitbucket repository, including issues and wiki.
mode: subagent
prompt: Use the 'archive-bitbucket-single' skill to archive the provided Bitbucket repository URL.
permission:
  skill:
    "archive-bitbucket-single": allow
  bash:
    "./bitbucket/archive_bitbucket_single.sh*": allow
---
## What I do
- Archives a specific Bitbucket repository, its wiki, and its issue tracker using `./bitbucket/archive_bitbucket_single.sh <url>`.

## When to use me
Use this when you need to ensure all components (git mirror, wiki, and issues) of a single Bitbucket repository are preserved.

## Usage Example
```bash
./bitbucket/archive_bitbucket_single.sh https://bitbucket.org/workspace/repo
```