#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.parse
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS


flags.DEFINE_string('archive_dir', None, 'Root directory for archives.')
flags.DEFINE_string('token_file', 'bitbucket_token.json', 'Path to file containing or to receive the access/refresh token.')
flags.DEFINE_string('client_creds_file', 'bitbucket_client.json', 'Path to file containing {"client_id": "...", "client_secret": "..."}.')
flags.DEFINE_string('org', None, 'Bitbucket organization (workspace) to archive.')
flags.DEFINE_string('repo', None, 'Specific repo to archive. If omitted, archives all repos in the org.')
flags.DEFINE_boolean('interactive_login', False, 'Trigger web browser to perform OAuth2 login and save token.')
flags.DEFINE_boolean('keep_going', False, 'Continue even if an error occurs during archival.')
flags.DEFINE_boolean('list', False, 'List all repositories in the organization and exit.')
flags.DEFINE_boolean('archive_wiki', True, 'Archive the wiki if it exists.')
flags.DEFINE_boolean('archive_issues', True, 'Archive the issues if they exist.')
flags.DEFINE_boolean('archive_metadata', True, 'Archive the repository metadata as JSON.')
flags.DEFINE_boolean('archive_repo', True, 'Archive the Git repository (mirror and reference clone).')

flags.DEFINE_alias('k', 'keep_going')
flags.DEFINE_alias('a', 'archive_dir')
flags.DEFINE_alias('t', 'token_file')
flags.DEFINE_alias('c', 'client_creds_file')
flags.DEFINE_alias('o', 'org')
flags.DEFINE_alias('r', 'repo')
flags.DEFINE_alias('i', 'interactive_login')
flags.DEFINE_alias('l', 'list')
flags.DEFINE_alias('w', 'archive_wiki')
flags.DEFINE_alias('u', 'archive_issues')
flags.DEFINE_alias('m', 'archive_metadata')
flags.DEFINE_alias('g', 'archive_repo')

flags.mark_flag_as_required('org')

# Globals for OAuth callback
OAUTH_CODE = None
OAUTH_SERVER = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global OAUTH_CODE
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'code' in query_components:
            OAUTH_CODE = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Login successful!</h1><p>You can close this tab and return to the terminal.</p></body></html>")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Error</h1><p>No code found in request.</p></body></html>")
        
        # Shutdown server asynchronously
        if OAUTH_SERVER:
            threading.Thread(target=OAUTH_SERVER.shutdown).start()

    def log_message(self, format, *args):
        pass  # Suppress HTTP server logging


def perform_interactive_login(client_id, client_secret):
    global OAUTH_SERVER, OAUTH_CODE
    port = int(os.environ.get('BITBUCKET_OAUTH_PORT', 8080))
    redirect_uri = f"http://localhost:{port}/callback"
    
    auth_url = f"https://bitbucket.org/site/oauth2/authorize?client_id={client_id}&response_type=code"
    
    OAUTH_SERVER = HTTPServer(('localhost', port), OAuthCallbackHandler)
    
    logging.info(f"Opening browser for interactive login: {auth_url}")
    webbrowser.open(auth_url)
    
    logging.info(f"Waiting for authorization callback on {redirect_uri} ...")
    OAUTH_SERVER.serve_forever()
    
    if not OAUTH_CODE:
        logging.fatal("Failed to obtain authorization code.")
        sys.exit(1)
        
    logging.info("Exchanging authorization code for access token...")
    response = requests.post(
        "https://bitbucket.org/site/oauth2/access_token",
        auth=(client_id, client_secret),
        data={
            "grant_type": "authorization_code",
            "code": OAUTH_CODE
        }
    )
    response.raise_for_status()
    token_data = response.json()
    token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
    
    with open(FLAGS.token_file, 'w') as f:
        json.dump(token_data, f)
        
    logging.info(f"Token saved to {FLAGS.token_file}")
    return token_data


def get_valid_token():
    if os.path.exists(FLAGS.token_file):
        with open(FLAGS.token_file, 'r') as f:
            try:
                token_data = json.load(f)
            except json.JSONDecodeError:
                token_data = None
    else:
        token_data = None

    if token_data and 'access_token' in token_data:
        # Check expiry
        if token_data.get('expires_at', 0) > time.time() + 60:
            return token_data['access_token']
        elif 'refresh_token' in token_data and os.path.exists(FLAGS.client_creds_file):
            logging.info("Access token expired, attempting refresh...")
            with open(FLAGS.client_creds_file, 'r') as f:
                creds = json.load(f)
            response = requests.post(
                "https://bitbucket.org/site/oauth2/access_token",
                auth=(creds['client_id'], creds['client_secret']),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": token_data['refresh_token']
                }
            )
            response.raise_for_status()
            new_token_data = response.json()
            new_token_data['expires_at'] = time.time() + new_token_data.get('expires_in', 3600)
            with open(FLAGS.token_file, 'w') as f:
                json.dump(new_token_data, f)
            return new_token_data['access_token']

    if FLAGS.interactive_login:
        if not os.path.exists(FLAGS.client_creds_file):
            logging.fatal(f"Interactive login requires client credentials file at {FLAGS.client_creds_file}")
            sys.exit(1)
        with open(FLAGS.client_creds_file, 'r') as f:
            creds = json.load(f)
        token_data = perform_interactive_login(creds['client_id'], creds['client_secret'])
        return token_data['access_token']
        
    logging.fatal("No valid token found and interactive login not requested. Run with --interactive_login.")
    sys.exit(1)


def api_get(endpoint, token, params=None):
    url = f"https://api.bitbucket.org/2.0/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_all_repos(org, token):
    repos = []
    endpoint = f"repositories/{org}"
    while endpoint:
        logging.info(f"Fetching repositories page...")
        if endpoint.startswith('https://'):
            url = endpoint
        else:
            url = f"https://api.bitbucket.org/2.0/{endpoint}"
            
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        repos.extend(data.get('values', []))
        endpoint = data.get('next')
    return repos


def clone_git_repo(repo_url, git_dest, repo_dir):
    # 1. Handle .git directory (mirror)
    if os.path.exists(git_dest):
        logging.info(f"Directory {git_dest} exists, attempting git fetch instead of clone...")
        subprocess.run(['git', 'fetch', '--all'], cwd=git_dest, check=True)
    else:
        logging.info(f"Cloning mirror to {git_dest} ...")
        os.makedirs(os.path.dirname(git_dest), exist_ok=True)
        subprocess.run(['git', 'clone', '--mirror', repo_url, git_dest], check=True)

    # 2. Handle non-.git directory (reference clone)
    if os.path.exists(repo_dir):
        logging.info(f"Directory {repo_dir} exists, attempting git fetch and pull instead of clone...")
        subprocess.run(['git', 'fetch', '--all'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'pull'], cwd=repo_dir, check=True)
    else:
        logging.info(f"Cloning with reference to {repo_dir} ...")
        ref_path = os.path.realpath(git_dest)
        subprocess.run(['git', 'clone', '--reference', ref_path, repo_url, repo_dir], check=True)


def archive_issues(org, repo_slug, token, dest_dir):
    zip_path = os.path.join(dest_dir, f"{repo_slug}_issues.zip")
    if os.path.exists(zip_path):
        logging.info(f"Issues archive already exists at {zip_path}, skipping export.")
        return

    logging.info(f"Requesting issues export for {repo_slug}...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    url = f"https://api.bitbucket.org/2.0/repositories/{org}/{repo_slug}/issues/export"
    
    # Start the export job
    response = requests.post(url, headers=headers, json={})
    
    if response.status_code not in (202, 200, 201):
        raise RuntimeError(f"Failed to trigger issues export: {response.text}")

    job_url = response.headers.get('Location')
    if not job_url:
        data = response.json()
        job_url = data.get('links', {}).get('self', {}).get('href')

    if not job_url:
        raise RuntimeError("Could not determine job polling URL from response.")

    logging.info("Export job started. Polling status...")
    
    while True:
        status_resp = requests.get(job_url, headers=headers)
        status_resp.raise_for_status()
        status_data = status_resp.json()
        
        phase = status_data.get('phase', status_data.get('status', 'UNKNOWN'))
        logging.info(f"Export phase: {phase} ...")
        
        if phase in ('COMPLETED', 'SUCCESS'):
            break
        elif phase in ('FAILED', 'ERROR'):
            raise RuntimeError(f"Issue export failed: {status_data}")
            
        time.sleep(5)

    # Download the zip
    # Bitbucket API typically provides the download link in the completed payload
    download_url = None
    if 'links' in status_data and 'export_result' in status_data['links']:
        download_url = status_data['links']['export_result']['href']
    else:
        # Fallback to appending /download or using job ID directly
        job_id = status_data.get('id') or job_url.rstrip('/').split('/')[-1]
        download_url = f"https://api.bitbucket.org/2.0/repositories/{org}/{repo_slug}/issues/export/{job_id}/export.zip"

    logging.info(f"Downloading issues zip from {download_url}...")
    zip_resp = requests.get(download_url, headers=headers, stream=True)
    if zip_resp.status_code == 200:
        zip_path = os.path.join(dest_dir, f"{repo_slug}_issues.zip")
        with open(zip_path, 'wb') as f:
            for chunk in zip_resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Saved issues archive to {zip_path}")
    else:
        raise RuntimeError(f"Failed to download zip: {zip_resp.status_code} - {zip_resp.text}")


def main(argv):
    del argv

    org = FLAGS.org
    target_repo = FLAGS.repo
    
    token = get_valid_token()

    if not FLAGS.archive_dir and os.environ.get('BITBUCKET_ARCHIVE_DIR'):
        # Support customization via environment variable as requested in AGENTS.md
        FLAGS.archive_dir = os.environ.get('BITBUCKET_ARCHIVE_DIR')

    if not FLAGS.archive_dir:
        if not FLAGS.interactive_login and not FLAGS.list:
            logging.fatal("Archive directory must be specified with --archive_dir.")
            sys.exit(1)

    if not os.path.exists(FLAGS.archive_dir):
        logging.info(f"Creating archive directory at {FLAGS.archive_dir}")
        os.makedirs(FLAGS.archive_dir, exist_ok=True)

    if FLAGS.interactive_login:
        logging.info("Interactive login completed/requested.")
        logging.info(f"Current archive directory is: {FLAGS.archive_dir}")
        logging.info("You can now run the script with --archive_dir if you wish to change it before starting archival.")
        return

    logging.info(f"Fetching repository list for organization: {org}")
    repos = get_all_repos(org, token)
    
    if target_repo:
        repos = [r for r in repos if r['slug'] == target_repo]
        if not repos:
            logging.error(f"Repository {target_repo} not found in org {org}")
            sys.exit(1)

    if FLAGS.list:
        for r in repos:
            print(r['slug'])
        return
            
    logging.info(f"Found {len(repos)} repositories to archive.")
    
    org_dir = os.path.join(FLAGS.archive_dir, org)
    os.makedirs(org_dir, exist_ok=True)
    
    for repo in repos:
        slug = repo['slug']
        logging.info(f"--- Processing repository: {slug} ---")
        
        # The non-.git directory is at org_dir/slug
        repo_dir = os.path.join(org_dir, slug)
        # The .git directory is at org_dir/slug.git
        git_dest = os.path.join(org_dir, f"{slug}.git")
        os.makedirs(repo_dir, exist_ok=True)
        
        # 1. Save metadata
        if FLAGS.archive_metadata:
            meta_path = os.path.join(repo_dir, f"{slug}_metadata.json")
            with open(meta_path, 'w') as f:
                json.dump(repo, f, indent=2)

        # Extract HTTPS clone URL (needed for repo and wiki)
        clone_url = None
        if FLAGS.archive_repo or FLAGS.archive_wiki:
            clone_url = next((link['href'] for link in repo['links']['clone'] if link['name'] == 'https'), None)
            if not clone_url:
                logging.error(f"No HTTPS clone URL found for {slug}")
                if not FLAGS.keep_going:
                    sys.exit(1)
                continue

        # 2. Clone Git Repo (Mirror + Reference clone)
        if FLAGS.archive_repo:
            try:
                clone_git_repo(clone_url, git_dest, repo_dir)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to clone repository {slug}: {e}")
                if not FLAGS.keep_going:
                    sys.exit(1)

        # 3. Clone Wiki (Mirror + Reference clone)
        if FLAGS.archive_wiki:
            if repo.get('has_wiki') and clone_url:
                wiki_url = clone_url.replace('.git', '.wiki.git')
                wiki_dest = os.path.join(org_dir, f"{slug}.wiki.git")
                wiki_repo_dir = os.path.join(org_dir, f"{slug}.wiki")
                try:
                    clone_git_repo(wiki_url, wiki_dest, wiki_repo_dir)
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to clone wiki for {slug}: {e}")
                    if not FLAGS.keep_going:
                        sys.exit(1)
            else:
                logging.info(f"No wiki found for {slug}")

        # 4. Archive Issues
        if FLAGS.archive_issues:
            if repo.get('has_issues'):
                try:
                    archive_issues(org, slug, token, repo_dir)
                except Exception as e:
                    logging.error(f"Failed to archive issues for {slug}: {e}")
                    if not FLAGS.keep_going:
                        sys.exit(1)
            else:
                logging.info(f"No issues found for {slug}")


    logging.info("Archival completed successfully.")


if __name__ == '__main__':
    if '-k' in sys.argv:
        FLAGS.keep_going = True
        sys.argv.remove('-k')
    app.run(main)
