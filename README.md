# PR Slack FrankAI Reviewer Trigger

A reusable GitHub Actions workflow that sends a Slack notification to `@Frank AI` when a pull request event occurs.

---

## 1. How It Works

1. A PR event in the caller repo triggers the caller workflow
2. The caller workflow invokes `pr_slack_frank_ai_reviewer_trigger.yml` in this repo via `workflow_call`, passing the PR URL
3. The reusable workflow runs `pr_slack_frank_ai_reviewer_trigger.py`
4. The script reads `SLACK_WEBHOOK_URL` and `FRANK_AI_MENTION`, then posts a Slack notification

Message format:
```
@Frank AI, please review the PR (https://github.com/owner/repo/pull/123).
```

---

## 2. Configuration (This Repo)

**Settings → Secrets and variables → Actions → Secrets**

| Secret | Required | Description |
|--------|----------|-------------|
| `SLACK_WEBHOOK_URL` | Yes | Slack Incoming Webhook URL (generated at api.slack.com/apps) |
| `FRANK_AI_MENTION` | No | Slack mention text — defaults to `@Frank AI` if unset or empty |

---

## 3. Calling from Another Repo

### 3.1 Prerequisites

1. This repo (`Owner_XXX/rk`) must be **public**, or both repos must be in the same organization
2. The caller repo must have `SLACK_WEBHOOK_URL` configured under **Settings → Secrets and variables → Actions → Secrets** (and optionally `FRANK_AI_MENTION`)
3. The caller repo must enable **Settings → Actions → General → Workflow permissions → Read and write permissions**

### 3.2 Configure Trigger Events

In the caller workflow, set the `types` list to the PR events you want to trigger the notification. Edit as needed:

```yaml
on:
  pull_request:
    # Available types — add or remove as needed:
    #   opened            - PR first created
    #   synchronize       - new commits pushed (can be noisy)
    #   reopened          - closed PR re-opened
    #   closed            - PR closed (merged or not)
    #   review_requested  - reviewer explicitly requested
    #   review_request_removed - reviewer removed
    #   ready_for_review  - draft converted to ready
    #   converted_to_draft - ready converted back to draft
    #   labeled           - label added
    #   unlabeled         - label removed
    #   assigned          - assignee added
    #   unassigned        - assignee removed
    types: [opened, reopened, ready_for_review, synchronize]
```

### 3.3 Add the Caller Workflow

Create `.github/workflows/pr_caller.yml` in the caller repo:

```yaml
name: PR Caller

on:
  pull_request:
    types: [opened, reopened, ready_for_review, synchronize]

jobs:
  call-frank-ai-notifier:
    uses: Owner_XXX/rk/.github/workflows/pr_slack_frank_ai_reviewer_trigger.yml@main
    secrets: inherit
    with:
      pr_url: ${{ github.event.pull_request.html_url }}
```

> `secrets: inherit` automatically passes the caller repo's secrets to the reusable workflow — no need to list them explicitly.

### 3.4 `uses` Path Reference

The `uses` field supports two path formats depending on where the caller workflow lives:

**Relative path** — only works when the caller and the reusable workflow are in the **same repo**:

```yaml
jobs:
  call-frank-ai-notifier:
    uses: ./.github/workflows/pr_slack_frank_ai_reviewer_trigger.yml
```

**Absolute path** — required when calling from a **different repo**:

```yaml
jobs:
  call-frank-ai-notifier:
    uses: Owner_XXX/rk/.github/workflows/pr_slack_frank_ai_reviewer_trigger.yml@main
```

The `@ref` suffix can be:

| Ref | Example | Notes |
|-----|---------|-------|
| Branch | `@main` | Always uses the latest commit on that branch |
| Tag | `@v1.0.0` | Pinned to a specific release |
| Commit SHA | `@abc1234` | Most stable — immune to branch updates |

---

## 4. Local Testing

```bash
pip install -r requirements.txt

export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export PR_URL=https://github.com/owner/repo/pull/1
export FRANK_AI_MENTION="@Frank AI"   # optional

python pr_slack_frank_ai_reviewer_trigger.py
```
