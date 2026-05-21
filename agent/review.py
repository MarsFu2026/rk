import os
import re
import sys
import json
import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
PR_NUMBER = os.environ["PR_NUMBER"]
REPO_FULL_NAME = os.environ["REPO_FULL_NAME"]
SCORE_THRESHOLD = int(os.environ.get("SCORE_THRESHOLD", "7"))

GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
GH_API = "https://api.github.com"

SYSTEM_PROMPT = """You are a senior software engineer reviewing a pull request against its design documentation.

Your tasks:
1. Read the linked requirement/design documents provided.
2. Read the PR description and diff.
3. Identify gaps: what the PR changes vs. what the design docs describe or omit.
4. Suggest concrete, actionable updates needed in the design doc to reflect the PR changes.
5. Score the alignment from 0 to 10:
   - 10 = the PR perfectly aligns with and is fully covered by the design docs
   - 7-9 = minor gaps, small doc updates needed
   - 4-6 = moderate gaps, several doc sections need updating
   - 1-3 = major gaps, the design doc is significantly out of date
   - 0 = no docs found, or the PR makes changes that completely contradict the design

Return ONLY valid JSON in this exact shape (no markdown fences, no extra keys):
{"score": <integer 0-10>, "suggestions": "<markdown string with bullet points>"}"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_pr_body() -> str:
    url = f"{GH_API}/repos/{REPO_FULL_NAME}/pulls/{PR_NUMBER}"
    resp = requests.get(url, headers=GH_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("body") or ""


def parse_doc_links(pr_body: str) -> list[str]:
    return re.findall(r"https?://[^\s\)\]\"'<]+", pr_body)


def gdoc_to_export_url(url: str) -> str:
    """Rewrite a Google Docs URL to its plain-text export endpoint."""
    match = re.search(r"docs\.google\.com/document/d/([^/]+)", url)
    if match:
        doc_id = match.group(1)
        return f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    return url


def fetch_document(url: str) -> str:
    url = gdoc_to_export_url(url)
    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "design-doc-review-agent/1.0"},
        )
        if resp.status_code != 200:
            print(f"  WARN: {url} returned {resp.status_code}, skipping")
            return ""
        return resp.text[:8000]
    except Exception as exc:
        print(f"  WARN: failed to fetch {url}: {exc}")
        return ""


def fetch_pr_diff() -> str:
    url = f"{GH_API}/repos/{REPO_FULL_NAME}/pulls/{PR_NUMBER}"
    diff_headers = {**GH_HEADERS, "Accept": "application/vnd.github.v3.diff"}
    resp = requests.get(url, headers=diff_headers, timeout=15)
    resp.raise_for_status()
    return resp.text[:6000]


def post_comment(body: str) -> None:
    url = f"{GH_API}/repos/{REPO_FULL_NAME}/issues/{PR_NUMBER}/comments"
    resp = requests.post(url, headers=GH_HEADERS, json={"body": body}, timeout=15)
    if resp.status_code not in (200, 201):
        print(f"  WARN: failed to post comment: {resp.status_code} {resp.text}")


def call_claude(pr_body: str, docs: dict[str, str], diff: str) -> tuple[int, str]:
    docs_section = ""
    if docs:
        for url, content in docs.items():
            docs_section += f"### {url}\n{content}\n\n"
    else:
        docs_section = "_No linked documents found in the PR description._\n"

    user_message = f"""## PR Description
{pr_body or '_No description provided._'}

## Linked Documents
{docs_section}
## PR Diff
```diff
{diff or '_No diff available._'}
```"""

    client = OpenAI(
        base_url="https://models.github.ai/inference",
        api_key=os.environ["MY_MODELS_TOKEN"],
    )
    message = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    raw = message.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
        score = int(parsed["score"])
        suggestions = str(parsed["suggestions"])
    except Exception:
        print(f"  WARN: could not parse Claude response as JSON, raw:\n{raw}")
        score = 0
        suggestions = raw

    return score, suggestions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Design Doc Review Agent starting — repo={REPO_FULL_NAME} PR=#{PR_NUMBER} threshold={SCORE_THRESHOLD}")

    print("Fetching PR body...")
    pr_body = fetch_pr_body()

    print("Parsing doc links...")
    links = parse_doc_links(pr_body)
    print(f"  Found {len(links)} link(s): {links}")

    print("Fetching documents...")
    docs: dict[str, str] = {}
    for url in links:
        content = fetch_document(url)
        if content:
            docs[url] = content
            print(f"  Fetched {len(content)} chars from {url}")

    print("Fetching PR diff...")
    diff = fetch_pr_diff()
    print(f"  Diff size: {len(diff)} chars")

    print("Calling Claude for review...")
    score, suggestions = call_claude(pr_body, docs, diff)
    print(f"  Score: {score}/10")

    result_icon = "✅" if score >= SCORE_THRESHOLD else "❌"
    comment = f"""## Design Doc Review {result_icon}

**Score: {score}/10** (threshold: {SCORE_THRESHOLD}/10)

### Suggestions
{suggestions}

---
*Posted by [Design Doc Review Agent](https://github.com/{REPO_FULL_NAME}/blob/main/.github/workflows/design-doc-review.yml)*"""

    print("Posting PR comment...")
    post_comment(comment)

    if score >= SCORE_THRESHOLD:
        print(f"PASS: score {score} >= threshold {SCORE_THRESHOLD}")
        sys.exit(0)
    else:
        print(f"FAIL: score {score} < threshold {SCORE_THRESHOLD}")
        sys.exit(1)


def build_slack_payload(event, pr):
    return {
        "text": f"PR #{pr['number']} [{event}]: {pr['title']}\n{pr['url']}"
    }


def main_slack_test() -> None:
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]

    pr = {
        "number":    os.environ["PR_NUMBER"],
    }
    event = os.environ["PR_ACTION"]  # opened / closed / review_requested ...

    payload = build_slack_payload(event, pr)

    resp = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    if resp.status_code != 200 or resp.text != "ok":
        raise RuntimeError(f"Slack notification failed: {resp.status_code} {resp.text}")

    print(f"Slack notification sent: PR #{pr['number']} [{event}]")

if __name__ == "__main__":
    main()
