---
name: archive-bitbucket-single
description: Archive a single Bitbucket repository, including issues and wiki.
license: MIT
---
## What I do
- Archives a specific Bitbucket repository, its wiki, and its issue tracker using `bitbucket/archive_bitbucket.py`.

## When to use me
Use this when you need to ensure all components (git mirror, wiki, and issues) of a single Bitbucket repository are preserved.

## Usage Example
```bash
python3 bitbucket/archive_bitbucket_single.sh https://bitbucket.org/workspace/repo
```