This directory, relative to project root at `./bitbucket`, needs to contain all
required to archive repos and issues for a bitbucket account -- whether person
or org.

Both repos and issues:

## Issues export

https://developer.atlassian.com/cloud/bitbucket/rest/api-group-issue-tracker/#api-repositories-workspace-repo-slug-issues-export-post

The following is relevant AUTHORITATIVE documentation from the above; some of
it may have been adapted for brevity and compactness:

> ```bash
> curl --request POST \
>   --url 'https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/issues/export' \
>   --header 'Authorization: Bearer <access_token>' \
>   --header 'Content-Type: application/json' \
>   --data '{
>   "type": "<string>",
>   "project_key": "<string>",
>   "project_name": "<string>",
>   "send_email": true,
>   "include_attachments": true
> }'
> ```
>
> A POST request to this endpoint initiates a new background celery task that archives the > repo's issues.
>
> When the job has been accepted, it will return a 202 (Accepted) along with a unique url to this job in the 'Location' response header. This url is the endpoint for where the user can obtain their zip files."
>
> ```bash
> curl --request GET \
>   --url 'https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/issues/export/{repo_name}-issues-{task_id}.zip' \
>   --header 'Authorization: Bearer <access_token>' \
>   --header 'Accept: application/json'
> ```
>
> Response:
>
> ```json
> {"type":"issue_job_status","status":"ACCEPTED","phase":"Initializing","total":0,"count":0,"pct":0}
> ```
>
> This endpoint is used to poll for the progress of an issue export job and return the zip file after the job is complete. As long as the job is running, this will return a 202 response with in the response body a description of the current status.
>
> After the job has been scheduled, but before it starts executing, the endpoint returns a 202 response with status `ACCEPTED`.
>
> Once it starts running, it is a 202 response with `status` `STARTED` and progress filled.
>
> After it is finished, it becomes a 200 response with status `SUCCESS` or `FAILURE`.
>
> ### Scopes
>
> ```
> OAuth 2.0 and Connect app scopes required:
> issue
> repository:admin
>
> API Token scopes required:
> read:issue:bitbucket
> ```

### More docs

Available scopes: https://developer.atlassian.com/cloud/bitbucket/rest/intro/#bitbucket-oauth-2-0-scopes

Announcement sunsetting issues and wikis August 20 2026 (very soon!): https://community.atlassian.com/forums/Bitbucket-articles/Announcing-sunset-of-Bitbucket-Issues-and-Wikis/ba-p/3193882?referer=https://community.atlassian.com/forums/Bitbucket-articles/Announcing-sunset-of-Bitbucket-Issues-and-Wikis/ba-p/3193882

Exporting issue data (does not focus on Jira Cloud despite URL): https://support.atlassian.com/bitbucket-cloud/docs/export-issue-data-to-jira-cloud/

Issue format: https://support.atlassian.com/bitbucket-cloud/docs/issue-import-and-export-data-format/

### Goals compared to initial requirements

Once the code is submitted, we need to:

1.  Make the location for storing Git archives customizable by an envvar when
    using a wrapper that defaults to the same as `./archive_sw.sh` (one repo)
    and `./archive_sw_ghorg.sh` (all GitHub org repos).
2.  Archive wikis too.
