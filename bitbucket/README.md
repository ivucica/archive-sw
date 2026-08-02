## Bitbucket Org Archiver

This tool archives Bitbucket repositories for a specific organization/workspace. It mirrors git repositories, saves repository metadata as JSON, downloads git wikis, and triggers/downloads issue archives in standard ZIP format.

### Prerequisites

1.  Install requirements:

    ```bash
    pip install -r requirements.txt
    ```

2.  Generate Bitbucket OAuth Client Credentials:

    *   Go to your Bitbucket settings: `Workspace settings` -> `OAuth consumers`.
    *   Click **Add consumer**.
    *   **Details**:
        *   Name*: `BitbucketArchiver` (or any name)
        *   Description: `Archives Bitbucket repositories, wikis, and issues.`
        *   URL: `http://localhost:8080`
    *   **Authorization**:
        *   [x] Authorization code
            *   [x] Refresh token (enabled by default when Auth code is checked)
        *   [ ] Client credentials
        *   **Callback URL***: `http://localhost:8080/callback` (Must match exactly).
    *   **Scopes**:
        *   Repositories: `Read`
        *   Issues: `Read`
        *   Wikis: `Read and write`
    *   Save and copy the **Key** (Client ID) and **Secret** (Client Secret).

3.  Create the credentials file:
    Save these credentials in a file named `bitbucket_client.json` in the same directory:

    ```json
    {
        "client_id": "YOUR_KEY_HERE",
        "client_secret": "YOUR_SECRET_HERE"
    }

### Usage

#### First run (Interactive Login)

To authorize the script, run it with the `--interactive_login` flag. It will open a browser, authenticate you, and save the refresh/access tokens to `bitbucket_token.json`.

```bash
python archive_bitbucket.py \
    --org=YOUR_WORKSPACE_ID \
    --interactive_login
```

#### Subsequent runs

If `bitbucket_token.json` exists, the script will read and refresh the token automatically.

```bash
# Archive all repos in the org into a custom directory
python archive_bitbucket.py \
    --org=YOUR_WORKSPACE_ID \
    --archive_dir=/opt/all_git_archives

# Archive a single repository
python archive_bitbucket.py \
    --org=YOUR_WORKSPACE_ID \
    --repo=SPECIFIC_REPO_SLUG
```

### Storage Structure

The script organizes files cleanly:

```
/opt/all_git_archives/
└── {workspace}/
    └── {repo_slug}/
        ├── {repo_slug}.git/             # Bare mirror of the main codebase
        ├── {repo_slug}.wiki.git/        # Bare mirror of the wiki codebase
        ├── {repo_slug}_metadata.json    # JSON metadata dump from Bitbucket API
        └── {repo_slug}_issues.zip       # Complete backup payload of issues and attachments
```
