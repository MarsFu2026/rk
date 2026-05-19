# Design Doc Review Agent

A GitHub Actions CI check that automatically reviews pull requests against linked design/requirement documents using Claude.

## How It Works

1. Developer opens or updates a PR — include links to design/requirement docs in the PR description
2. The CI check triggers, fetches those documents, reads the PR diff
3. Claude analyzes alignment and produces suggestions + a score (0–10)
4. Results are posted as a PR comment
5. If `score >= SCORE_THRESHOLD` → check passes (green); otherwise → check fails (blocks merge)

## Setup

### 1. Push this repo to GitHub

The workflow file must be on the default branch (`main`) to activate.

### 2. Add the Anthropic API Key

**Repo → Settings → Secrets and variables → Actions → Secrets tab**

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your key from console.anthropic.com |

### 3. Set the Score Threshold (optional, default = 7)

**Repo → Settings → Secrets and variables → Actions → Variables tab**

| Name | Value |
|---|---|
| `SCORE_THRESHOLD` | `7` (integer 0–10) |

Change this at any time — takes effect on the next PR trigger.

### 4. Allow the workflow to post PR comments

**Repo → Settings → Actions → General → Workflow permissions**

Select **"Read and write permissions"** → Save

### 5. Configure Branch Protection to enforce the check

**Repo → Settings → Branches → Add branch protection rule**

- Branch pattern: `main`
- Enable: **"Require status checks to pass before merging"**
- Add status check: `design-doc-review`
  _(must have run at least once before it appears in the search — open a test PR first)_

### 6. Target a Different Repo (optional)

By default the agent reviews PRs in the repo where the workflow lives. To point it at another repo:

**Repo → Settings → Secrets and variables → Actions → Variables tab**

| Name | Value |
|---|---|
| `TARGET_REPO` | `owner/other-repo` |

For cross-repo access, also add a PAT with `repo` scope as `secrets.GH_PAT` and update the workflow to use it instead of `secrets.GITHUB_TOKEN`.

## Writing PR Descriptions for Best Results

Include direct links to your design and requirement documents in the PR body:

```
## Changes
- Added user authentication flow

## Design Docs
- [Requirements](https://docs.google.com/document/d/YOUR_DOC_ID/edit)
- [Design Doc](https://docs.google.com/document/d/YOUR_DOC_ID/edit)
```

The agent extracts all `https://` links from the PR description automatically.

**Supported document types:**
- Google Docs (public) — auto-converted to plain text export
- Any other public URL (GitHub raw files, Confluence public pages, etc.)

**Not supported (POC limitation):**
- Private Google Docs / Notion pages (requires OAuth)

## Local Testing

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
export PR_NUMBER=1
export REPO_FULL_NAME=owner/repo
export SCORE_THRESHOLD=7

python agent/review.py
```
