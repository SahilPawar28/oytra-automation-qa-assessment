# Automation & QA Developer — Take-Home Assessment

**Submitted by:** Sahil Pawar
**Loom walkthrough:** _[link to be added]_

## What's in this repo

| Folder | Contents |
|---|---|
| [`submission/task1`](submission/task1) | QA & Debug Report on the RealWorld "Conduit" demo app — bug table, root-cause analysis, screenshots |
| [`submission/task2`](submission/task2) | n8n workflow: GitHub trending-repo digest with enrichment, conditional routing, error handling, and email output |
| [`submission/bonus`](submission/bonus) | n8n uptime monitor for the Task 1 app, with retry logic, response-time tracking, and a daily summary |

## Summary of approach

**Task 1** — I tested the live RealWorld demo app (`demo.realworld.show`; the assignment's original link was dead) at two levels: the normal UI flow, and direct API calls once I noticed the frontend and backend disagreed on a few things. That's where the strongest finding came from — a password-validation rule enforced on one endpoint (`PUT /api/user`) but completely absent on another (`POST /api/users`), proven with raw request/response pairs, not guesswork. I also checked what the app gets *right* (server-side authorization, no user enumeration, safe XSS handling) so the report isn't one-sided.

**Task 2** — Built entirely in n8n Cloud (chose Cloud over local since disk space was tight). Schedule trigger → GitHub Search API (top 5 repos by stars for a topic) → enrichment call per repo (fetches each README) → IF-branch on a star threshold → one consolidated HTML digest → real email via SMTP. The enrichment step uses n8n's "Continue (using error output)" so a single failed API call degrades gracefully into a fallback message instead of crashing the whole run or vanishing silently — verified by inspecting what that error branch actually contains, not assumed.

**Bonus** — A second workflow pings the Task 1 app every 5 minutes, with real retry logic (up to 3 attempts) and response-time tracking built into the check itself, alerting by email on any non-200 response. It also accumulates stats between runs (via n8n's workflow static data) and emails a daily uptime summary on a separate schedule, resetting the counters afterward.

Both n8n workflows are fully built and tested (executed successfully end-to-end, including a real email delivered) but left **unpublished/inactive** in n8n Cloud, since activating them would start consuming the account's free execution quota for a submission that's reviewed manually rather than run continuously.

## Tools used
Documentation, browser-based testing, and n8n workflow construction were done with AI assistance (Claude), as explicitly permitted by the assignment. Every API call, node configuration, and root-cause claim in the reports was independently verified (via curl/browser testing) rather than taken on faith — happy to walk through the reasoning behind any specific choice.
