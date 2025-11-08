#!/usr/bin/env python3
"""
Update milestone progress status.

Queries GitHub API for milestone issues, computes completion percentage,
and generates a status markdown file with blocking issues and timeline.
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


def get_milestone_data(owner: str, repo: str, milestone_number: int, token: str) -> dict[str, Any]:
    """Fetch milestone data from GitHub API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get milestone details
    milestone_url = f"https://api.github.com/repos/{owner}/{repo}/milestones/{milestone_number}"
    response = requests.get(milestone_url, headers=headers, timeout=30)
    response.raise_for_status()
    milestone = response.json()

    # Get issues for milestone
    issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {"milestone": str(milestone_number), "state": "all", "per_page": 100}
    response = requests.get(issues_url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    issues = response.json()

    return {"milestone": milestone, "issues": issues}


def compute_progress(data: dict[str, Any]) -> dict[str, Any]:
    """Compute milestone progress statistics."""
    issues = data["issues"]
    milestone = data["milestone"]

    total = len(issues)
    closed = sum(1 for issue in issues if issue["state"] == "closed")
    open_count = total - closed
    percentage = (closed / total * 100) if total > 0 else 0

    # Find blocking issues (open issues with no recent activity)
    now = datetime.utcnow()
    blocking = []
    for issue in issues:
        if issue["state"] == "open":
            updated = datetime.strptime(issue["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            days_stale = (now - updated).days
            if days_stale > 7:  # Consider stale after 7 days
                blocking.append(
                    {
                        "number": issue["number"],
                        "title": issue["title"],
                        "url": issue["html_url"],
                        "days_stale": days_stale,
                    }
                )

    due_date = milestone.get("due_on")
    if due_date:
        due = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%SZ")
        days_remaining = (due - now).days
    else:
        days_remaining = None

    return {
        "total": total,
        "closed": closed,
        "open": open_count,
        "percentage": percentage,
        "blocking": blocking,
        "days_remaining": days_remaining,
        "due_date": due_date,
        "title": milestone["title"],
        "url": milestone["html_url"],
    }


def generate_status_markdown(progress: dict[str, Any], issues: list[dict[str, Any]]) -> str:
    """Generate status markdown content."""
    lines = [
        f"# Milestone Progress: {progress['title']}",
        "",
        f"**Progress:** {progress['closed']}/{progress['total']} issues closed ({progress['percentage']:.1f}%)",
        "",
    ]

    if progress["days_remaining"] is not None:
        if progress["days_remaining"] > 0:
            lines.append(f"**Timeline:** {progress['days_remaining']} days remaining until {progress['due_date'][:10]}")
        else:
            lines.append(f"**Timeline:** ⚠️ Overdue by {abs(progress['days_remaining'])} days")
        lines.append("")

    lines.append(f"**Milestone:** [{progress['title']}]({progress['url']})")
    lines.append("")

    # Progress bar
    bar_length = 20
    filled = int(progress["percentage"] / 100 * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    lines.append(f"```\n{bar} {progress['percentage']:.1f}%\n```")
    lines.append("")

    # Open issues
    lines.append("## Open Issues")
    lines.append("")
    open_issues = [i for i in issues if i["state"] == "open"]
    if open_issues:
        for issue in open_issues:
            lines.append(f"- [#{issue['number']} {issue['title']}]({issue['html_url']})")
    else:
        lines.append("✅ All issues completed!")
    lines.append("")

    # Blocking/stale issues
    if progress["blocking"]:
        lines.append("## ⚠️ Stale Issues (>7 days)")
        lines.append("")
        for block in progress["blocking"]:
            lines.append(f"- [#{block['number']} {block['title']}]({block['url']}) — {block['days_stale']} days stale")
        lines.append("")

    # Closed issues
    lines.append("## Completed Issues")
    lines.append("")
    closed_issues = [i for i in issues if i["state"] == "closed"]
    if closed_issues:
        for issue in closed_issues:
            lines.append(f"- [#{issue['number']} {issue['title']}]({issue['html_url']})")
    else:
        lines.append("*No issues completed yet*")
    lines.append("")

    lines.append(f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update milestone progress status")
    parser.add_argument("--milestone", type=int, required=True, help="Milestone number")
    parser.add_argument("--status-file", type=str, required=True, help="Output status markdown file")
    parser.add_argument("--owner", type=str, default="georgicaradu5-source", help="Repository owner")
    parser.add_argument("--repo", type=str, default="Play-stuff", help="Repository name")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        return 1

    try:
        # Fetch milestone data
        print(f"Fetching milestone {args.milestone} from {args.owner}/{args.repo}...")
        data = get_milestone_data(args.owner, args.repo, args.milestone, token)

        # Compute progress
        progress = compute_progress(data)
        print(f"Progress: {progress['closed']}/{progress['total']} ({progress['percentage']:.1f}%)")

        # Generate markdown
        markdown = generate_status_markdown(progress, data["issues"])

        # Write status file
        status_path = Path(args.status_file)
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(markdown, encoding="utf-8")
        print(f"Status written to {status_path}")

        return 0

    except requests.exceptions.RequestException as e:
        print(f"Error fetching milestone data: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
