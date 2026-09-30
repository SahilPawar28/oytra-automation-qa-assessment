# Task 2 — n8n API Integration Workflow

**Workflow name:** Task2_Workflow_SahilPawar
**Platform:** n8n Cloud

## What it does
Every hour (Schedule Trigger), the workflow pulls trending GitHub repos for the topic `automation`, keeps the top 5 by star count, enriches each one with its README, tags each repo as "High Impact" or "Emerging" based on a star threshold, builds one consolidated HTML digest, and emails it.

## APIs used and why
- **GitHub Search API** (`GET /search/repositories?q=topic:automation&sort=stars&order=desc`) — free, no auth/API key required for this volume of requests, and returns exactly the kind of "trending repos for a topic" data the assignment suggested. I picked the `automation` topic since it's thematically close to this role (n8n itself shows up as the #1 result, which felt like a fitting coincidence).
- **GitHub Repository Contents API** (`GET /repos/{owner}/{repo}/readme` with `Accept: application/vnd.github.raw`) — the second, enrichment call. For every one of the top-5 repos, it fetches the actual README content so the digest includes a real content excerpt, not just metadata.

## Transformation
A Code node sorts the raw search results by `stargazers_count` descending and keeps only the top 5, remapping each into a clean shape (`name`, `full_name`, `owner`, `html_url`, `description`, `stars`, `language`). A second Code node merges the fetched README text back onto each repo's record.

## Conditional branch
An IF node checks `stars > 1000`. Items on the true branch get tagged `tier: "High Impact (over 1000 stars)"`; items on the false branch get tagged `tier: "Emerging (1000 stars or fewer)"`. Both branches re-merge into one list before the final digest is built, so the email always contains all 5 repos, just labeled differently — this demonstrates the routing without silently dropping any results.

## Output
A Code node builds a single HTML table (one row per repo: name, star count, tier, description, link, README excerpt) and a **Send Email** node (SMTP) delivers it. Credentials are stored in n8n's own Credentials store (a Gmail App Password behind an SMTP credential) and referenced by ID — nothing is hardcoded in the workflow JSON.

## Error handling (how the error path behaves)
The README-fetch HTTP Request node is set to **"Continue (using error output)"** instead of the default "Stop Workflow" or plain "Continue." This gives it two separate outputs:
- **Success** → merged normally with the repo data.
- **Error** → routed to a dedicated fallback Code node that reconstructs the original repo fields (via `$('Filter Top 5 by Stars')`) and sets `readme_excerpt` to `"README fetch failed: <error message>"` instead of leaving the item blank or crashing the whole run.

Both paths are recombined with a Merge node (Append mode) before continuing, so **a single failed API call degrades gracefully** — that repo still appears in the digest with a visible "fetch failed" note — rather than silently disappearing or taking down the entire workflow. I verified this design by inspecting what the HTTP Request node's error output actually contains (rather than guessing), and by running the full workflow end-to-end to confirm both the success path and the merge logic work with real data.

## Why a Schedule Trigger over a Webhook
The assignment allows either. I chose Schedule (hourly) since the scenario described is literally a recurring "morning brief" — a cron-style job is the more natural real-world fit than something that needs to be triggered externally via curl/Postman every time.
