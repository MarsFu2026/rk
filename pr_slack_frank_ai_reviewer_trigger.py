import os
import json
import requests

FRANK_AI_MENTION = os.environ.get("FRANK_AI_MENTION") or "@Frank AI"


def build_slack_payload(pr_url: str) -> dict:
    return {
        "text": f"{FRANK_AI_MENTION}, please review the PR ({pr_url})."
    }


def main() -> None:
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    pr_url = os.environ["PR_URL"]

    payload = build_slack_payload(pr_url)
    resp = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if resp.status_code != 200 or resp.text != "ok":
        raise RuntimeError(f"Slack notification failed: {resp.status_code} {resp.text}")
    print(f"Slack notification sent: {pr_url}")


if __name__ == "__main__":
    main()
