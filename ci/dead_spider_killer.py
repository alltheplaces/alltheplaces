#!/usr/bin/env python3
"""
Dead Spider Killer - Automatically detect and remove spiders that consistently produce 0 results.

Fetches run history from data.alltheplaces.xyz, identifies spiders with 0 features
across N consecutive runs, classifies the failure mode, and creates removal PRs
or investigation issues as appropriate.

See: https://github.com/alltheplaces/alltheplaces/issues/9885
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from enum import Enum
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

HISTORY_URL = "https://data.alltheplaces.xyz/runs/history.json"
DATA_BASE_URL = "https://alltheplaces-data.openaddresses.io"

# Reuse connections across requests
session = requests.Session()
session.headers["User-Agent"] = "AllThePlaces Dead Spider Killer (+https://github.com/alltheplaces/alltheplaces)"


class FailureType(Enum):
    TIMEOUT = "timeout"
    ZYTE_PROXY = "zyte_proxy"
    NEEDS_PROXY = "needs_proxy"
    DNS_FAILURE = "dns_failure"
    SITE_GONE_404 = "site_gone_404"
    PARSE_ERROR = "parse_error"
    SPIDER_EXCEPTION = "spider_exception"
    NO_RESPONSE = "no_response"
    REDIRECT_ONLY = "redirect_only"
    CONNECTION_REFUSED = "connection_refused"
    HTTP_ERROR = "http_error"
    SITE_CHANGED = "site_changed"
    UNKNOWN = "unknown"


# Which failure types should result in a removal PR (site is truly gone)
PR_FAILURES = {
    FailureType.DNS_FAILURE,
    FailureType.CONNECTION_REFUSED,
    FailureType.NO_RESPONSE,
}
# Which failure types should result in an investigation issue (potentially fixable)
ISSUE_FAILURES = {
    FailureType.SITE_GONE_404,
    FailureType.PARSE_ERROR,
    FailureType.SPIDER_EXCEPTION,
    FailureType.REDIRECT_ONLY,
    FailureType.HTTP_ERROR,
    FailureType.SITE_CHANGED,
    FailureType.NEEDS_PROXY,
    FailureType.UNKNOWN,
}
# Which failure types are skipped entirely
SKIP_FAILURES = {FailureType.TIMEOUT, FailureType.ZYTE_PROXY}


def fetch_recent_runs(n):
    """Fetch the last N runs from history.json."""
    logger.info("Fetching run history from %s", HISTORY_URL)
    resp = session.get(HISTORY_URL, timeout=30)
    resp.raise_for_status()
    history = resp.json()
    runs = history[-n:]
    logger.info("Found %d total runs, using last %d", len(history), len(runs))
    return runs


def fetch_run_results(stats_url):
    """Fetch a run's _results.json and return the results list."""
    logger.info("Fetching results from %s", stats_url)
    resp = session.get(stats_url, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


def find_dead_spiders(runs):
    """Find spiders that produced 0 features in ALL of the given runs.

    Returns a dict of {spider_name: {"filename": str, "run_history": [{run_id, features, errors}]}}
    Only includes spiders that were present in every run and had 0 features each time.
    """
    # Build per-spider history across all runs
    spider_data = {}
    run_ids = []

    for run in runs:
        run_id = run["run_id"]
        run_ids.append(run_id)
        results = fetch_run_results(run["stats_url"])

        for entry in results:
            name = entry["spider"]
            if name not in spider_data:
                spider_data[name] = {"filename": entry.get("filename", ""), "runs": {}}
            spider_data[name]["runs"][run_id] = {
                "features": entry.get("features", 0),
                "errors": entry.get("errors", 0),
                "elapsed_time": entry.get("elapsed_time", 0),
            }

    # Filter to spiders present in ALL runs with 0 features each time
    dead_spiders = {}
    for name, data in spider_data.items():
        # Must be present in every run
        if len(data["runs"]) != len(run_ids):
            continue
        # Must have 0 features in every run
        if all(r["features"] == 0 for r in data["runs"].values()):
            dead_spiders[name] = {
                "filename": data["filename"],
                "run_history": [{"run_id": rid, **data["runs"][rid]} for rid in run_ids],
            }

    logger.info("Found %d spiders with 0 features across all %d runs", len(dead_spiders), len(run_ids))
    return dead_spiders


def has_skip_flag(filename):
    """Check if a spider file has skip_auto_delete = True."""
    path = Path(__file__).parent.parent / filename
    if not path.exists():
        return False
    content = path.read_text()
    return bool(re.search(r"skip_auto_delete\s*=\s*True", content))


def has_requires_proxy(filename):
    """Check if a spider file has requires_proxy set."""
    path = Path(__file__).parent.parent / filename
    if not path.exists():
        return False
    content = path.read_text()
    return bool(re.search(r'requires_proxy\s*=\s*(?:True|"[^"]*"|\'[^\']*\')', content))


def fetch_spider_stats(run_id, spider_name):
    """Fetch the individual stats JSON for a spider from a specific run."""
    url = f"{DATA_BASE_URL}/runs/{run_id}/stats/{spider_name}.json"
    logger.debug("Fetching spider stats from %s", url)
    resp = session.get(url, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def _extract_evidence(stats):
    """Extract status codes, exceptions, and other evidence from Scrapy stats."""
    evidence = {}

    status_codes = {}
    for key, value in stats.items():
        m = re.match(r"downloader/response_status_count/(\d+)", key)
        if m:
            status_codes[int(m.group(1))] = value
    evidence["status_codes"] = status_codes

    exceptions = {}
    for key, value in stats.items():
        for prefix in ("downloader/exception_type_count/", "spider_exceptions/"):
            if key.startswith(prefix):
                exceptions[key[len(prefix) :]] = value
    evidence["exceptions"] = exceptions

    evidence["finish_reason"] = stats.get("finish_reason", "")
    evidence["elapsed_time"] = stats.get("elapsed_time_seconds", 0)
    evidence["full_stats"] = stats

    return evidence


def _sum_matching(mapping, *patterns):
    """Sum values in a dict where any pattern appears in the key."""
    return sum(v for k, v in mapping.items() if any(p in k for p in patterns))


def _classify_from_evidence(evidence, filename):  # noqa: C901
    """Classify failure type from extracted evidence. Order matters."""
    status_codes = evidence["status_codes"]
    exceptions = evidence["exceptions"]
    stats = evidence["full_stats"]

    total_requests = sum(status_codes.values()) + sum(exceptions.values())
    count_404 = status_codes.get(404, 0)

    # Estimated non-robots content responses
    non_robots_200 = max(0, status_codes.get(200, 0) - 1)
    content_responses = non_robots_200 + sum(c for code, c in status_codes.items() if code != 200)

    # 1. Timeout
    if stats.get("finish_reason") == "closespider_timeout":
        return FailureType.TIMEOUT
    timeout_errors = _sum_matching(exceptions, "TimeoutError", "TCPTimedOutError")
    if timeout_errors > 0 and total_requests > 0 and timeout_errors / total_requests > 0.5:
        return FailureType.TIMEOUT

    # 2. Zyte/proxy issue
    if any("zyte" in k.lower() for k in stats) and has_requires_proxy(filename):
        return FailureType.ZYTE_PROXY

    # 3. DNS failure
    if _sum_matching(exceptions, "DNSLookupError") > 0:
        return FailureType.DNS_FAILURE

    # 4. Parse errors
    if _sum_matching(exceptions, "JSONDecodeError", "XMLSyntaxError", "ParserError", "ValueError") > 0:
        return FailureType.PARSE_ERROR

    # 5. Site gone (404)
    if count_404 > 0 and content_responses > 0 and count_404 / content_responses > 0.5:
        return FailureType.SITE_GONE_404

    # 6. Connection refused / response never received
    conn_errors = _sum_matching(
        exceptions, "ConnectionRefusedError", "ResponseNeverReceived", "ResponseFailed", "NotSupported"
    )
    if conn_errors > 0 and total_requests > 0 and conn_errors / total_requests > 0.5:
        return FailureType.CONNECTION_REFUSED

    # 7. Spider code exceptions
    if _sum_matching(exceptions, "KeyError", "TypeError", "AttributeError", "IndexError", "UnboundLocalError") > 0:
        return FailureType.SPIDER_EXCEPTION

    # 8. Needs proxy
    if status_codes.get(403, 0) + status_codes.get(429, 0) > 0 and not has_requires_proxy(filename):
        return FailureType.NEEDS_PROXY

    # 9. Redirect-only
    redirect_count = sum(status_codes.get(c, 0) for c in (301, 302, 307, 308))
    real_200 = status_codes.get(200, 0) - min(status_codes.get(200, 0), 2)
    if redirect_count > 0 and real_200 == 0 and count_404 == 0:
        return FailureType.REDIRECT_ONLY

    # 10. HTTP error codes as dominant response
    error_responses = sum(c for code, c in status_codes.items() if code >= 400)
    if error_responses > 0 and content_responses > 0 and error_responses / content_responses > 0.5:
        return FailureType.HTTP_ERROR

    # 11. No responses at all or only robots.txt
    if not status_codes and not exceptions:
        return FailureType.NO_RESPONSE
    if status_codes.get(200, 0) <= 2 and len(status_codes) <= 1 and not exceptions:
        return FailureType.NO_RESPONSE

    # 12. IgnoreRequest - middleware rejected all requests
    if _sum_matching(exceptions, "IgnoreRequest") > 0 and status_codes.get(200, 0) <= 2:
        return FailureType.SITE_CHANGED

    # 13. Zyte API errors without requires_proxy
    if _sum_matching(exceptions, "zyte") > 0:
        return FailureType.CONNECTION_REFUSED

    # 14. Site changed - got 200s but found no items
    if status_codes.get(200, 0) > 2 and not exceptions:
        return FailureType.SITE_CHANGED

    return FailureType.UNKNOWN


def classify_failure(spider_name, filename, run_id):
    """Classify why a spider is producing 0 results.

    Returns (FailureType, evidence_dict).
    """
    stats = fetch_spider_stats(run_id, spider_name)
    if stats is None:
        return FailureType.UNKNOWN, {"reason": "Stats file not found"}

    evidence = _extract_evidence(stats)
    classification = _classify_from_evidence(evidence, filename)
    return classification, evidence


def _is_only_robots(stats):
    """Check if the only 200 responses are likely robots.txt."""
    # If there are very few 200s (1-2) and the spider got 0 items,
    # those 200s are probably just robots.txt
    return stats.get("downloader/response_status_count/200", 0) <= 2


def _existing_pr_or_issue(spider_name):
    """Check if there's already a recent PR or issue for this spider.

    Checks for open or recently closed PRs (by branch name) and open issues
    (by exact title match) to avoid creating duplicates across multiple runs.
    """
    branch = f"dead-spider/{spider_name}"

    # Check for open or recently closed/merged PRs on this branch
    for state in ("open", "closed", "merged"):
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                state,
                "--json",
                "number,closedAt,mergedAt",
                "--limit",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            prs = json.loads(result.stdout)
            if prs:
                logger.info("PR already exists for %s (%s): #%d", spider_name, state, prs[0]["number"])
                return True

    # Check for open issues with exact title match
    # Search is fuzzy, so we fetch candidates and filter for exact match
    pr_title = f"Dead spider: `{spider_name}` —"
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--search",
            f"{spider_name} in:title",
            "--state",
            "open",
            "--json",
            "number,title",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        issues = json.loads(result.stdout)
        for issue in issues:
            if issue["title"].startswith(pr_title):
                logger.info("Issue already exists for %s: #%d", spider_name, issue["number"])
                return True

    return False


FAILURE_EXPLANATIONS = {
    FailureType.DNS_FAILURE: {
        "title": "DNS lookup failure",
        "explanation": "The domain name for this spider's website no longer resolves. The site appears to have been taken offline entirely.",
        "suggestion": None,
    },
    FailureType.CONNECTION_REFUSED: {
        "title": "Connection refused",
        "explanation": "The server actively refused connections or never sent a response. The site appears to be down or blocking all traffic.",
        "suggestion": None,
    },
    FailureType.NO_RESPONSE: {
        "title": "No usable response",
        "explanation": "The spider received no meaningful responses (at most a robots.txt). The target endpoint appears to no longer exist.",
        "suggestion": None,
    },
    FailureType.SITE_GONE_404: {
        "title": "HTTP 404 (Not Found)",
        "explanation": "The spider's target URLs are returning 404 errors. The pages may have moved to new URLs.",
        "suggestion": "Check if the website has restructured its URLs or moved its store locator to a new path.",
    },
    FailureType.REDIRECT_ONLY: {
        "title": "Redirect with no content",
        "explanation": "The spider's target URLs are redirecting (301/302) but the redirected pages don't contain any scrapeable data.",
        "suggestion": "Check where the URLs redirect to — the site may have moved its store locator to a new domain or path that needs updating in the spider.",
    },
    FailureType.HTTP_ERROR: {
        "title": "HTTP server errors",
        "explanation": "The spider is getting error responses (4xx/5xx) from the server.",
        "suggestion": "Check if the API endpoint has changed, requires new headers, or if the server is returning errors for a specific reason (rate limiting, authentication, etc.).",
    },
    FailureType.PARSE_ERROR: {
        "title": "Response parsing failure",
        "explanation": "The spider received responses but failed to parse them. The site may have changed its response format (e.g. from JSON to HTML, or changed its JSON schema).",
        "suggestion": "Visit the site and check what format the store locator API returns now. The spider's parsing logic likely needs updating to match.",
    },
    FailureType.SPIDER_EXCEPTION: {
        "title": "Spider code exception",
        "explanation": "The spider's own code is crashing with an unhandled exception. The site likely changed its page structure or API response format in a way the spider doesn't handle.",
        "suggestion": "Look at the exception type and the spider's source code to understand what data the spider expected vs. what the site now returns.",
    },
    FailureType.SITE_CHANGED: {
        "title": "Site changed (no items found)",
        "explanation": "The spider successfully fetched pages (HTTP 200) but found no items to extract. The site's HTML structure or API response format has likely changed.",
        "suggestion": "Visit the site and compare its current structure to what the spider expects. The CSS selectors, XPath expressions, or JSON paths in the spider probably need updating.",
    },
    FailureType.NEEDS_PROXY: {
        "title": "Blocked by bot protection",
        "explanation": "The spider is getting 403 Forbidden or 429 Too Many Requests responses, suggesting the site is blocking automated access.",
        "suggestion": "Try adding `requires_proxy = True` to the spider class to route requests through the Zyte proxy.",
    },
    FailureType.UNKNOWN: {
        "title": "Unknown failure",
        "explanation": "The spider is producing 0 results but the failure mode doesn't match any known pattern.",
        "suggestion": "Manual investigation is needed. Check the spider source code and try running it locally to diagnose the issue.",
    },
}


def _format_evidence_summary(evidence):
    """Format evidence into a human-readable summary."""
    lines = []

    status_codes = evidence.get("status_codes", {})
    if status_codes:
        codes_str = ", ".join(f"{code}: {count}" for code, count in sorted(status_codes.items()))
        lines.append(f"**Response status codes**: {codes_str}")

    exceptions = evidence.get("exceptions", {})
    if exceptions:
        exc_str = ", ".join(f"`{exc}`: {count}" for exc, count in sorted(exceptions.items()))
        lines.append(f"**Exceptions**: {exc_str}")

    elapsed = evidence.get("elapsed_time", 0)
    lines.append(f"**Elapsed time**: {elapsed:.1f}s")

    return "\n".join(lines)


def _format_run_history_table(run_history, spider_name):
    """Format run history as a markdown table with links to stats and logs."""
    lines = ["| Run | Features | Errors | Elapsed | Links |", "|-----|----------|--------|---------|-------|"]
    for entry in run_history:
        run_url = f"{DATA_BASE_URL}/runs/{entry['run_id']}"
        links = f"[stats]({run_url}/stats/{spider_name}.json) · [log]({run_url}/logs/{spider_name}.txt)"
        lines.append(
            f"| {entry['run_id']} | {entry['features']} | {entry['errors']} | {entry['elapsed_time']:.0f}s | {links} |"
        )
    return "\n".join(lines)


def create_removal_pr(spider_name, filename, classification, evidence, run_history, dry_run=False):
    """Create a PR to remove a dead spider."""
    if _existing_pr_or_issue(spider_name):
        return False

    branch = f"dead-spider/{spider_name}"
    repo_root = Path(__file__).parent.parent
    spider_path = repo_root / filename

    if not spider_path.exists():
        logger.warning("Spider file not found: %s", filename)
        return False

    info = FAILURE_EXPLANATIONS[classification]
    evidence_summary = _format_evidence_summary(evidence)
    history_table = _format_run_history_table(run_history, spider_name)
    full_stats_json = json.dumps(evidence.get("full_stats", {}), indent=2, default=str)

    pr_body = f"""## {info["title"]}

{info["explanation"]}

This spider has produced **0 results for {len(run_history)} consecutive runs**.

### Evidence from latest run
{evidence_summary}

### Run history
{history_table}

<details>
<summary>Full stats JSON from latest run</summary>

```json
{full_stats_json}
```
</details>
"""

    if dry_run:
        logger.info("[DRY RUN] Would create removal PR for %s (%s)", spider_name, classification.value)
        return True

    # Save current branch to return to it later
    current_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()

    try:
        # Create branch from master, deleting any stale local branch first
        subprocess.run(["git", "checkout", "master"], check=True, capture_output=True)
        subprocess.run(["git", "branch", "-D", branch], capture_output=True)  # ignore if doesn't exist
        subprocess.run(["git", "checkout", "-b", branch], check=True, capture_output=True)

        # Remove spider file
        subprocess.run(["git", "rm", str(spider_path)], check=True, capture_output=True)

        # Also remove test file if it exists
        test_path = repo_root / "tests" / f"test_{spider_path.name}"
        if test_path.exists():
            subprocess.run(["git", "rm", str(test_path)], check=True, capture_output=True)

        # Commit
        subprocess.run(
            ["git", "commit", "-m", f"Remove dead spider: {spider_name}"],
            check=True,
            capture_output=True,
        )

        # Push
        subprocess.run(["git", "push", "-u", "origin", branch], check=True, capture_output=True)

        # Create PR
        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                f"Remove dead spider: `{spider_name}` — {info['title']}",
                "--body",
                pr_body,
                "--label",
                "automated:dead-spider-removal",
                "--base",
                "master",
                "--head",
                branch,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error("Failed to create PR for %s: %s", spider_name, result.stderr)
            return False

        logger.info("Created PR for %s: %s", spider_name, result.stdout.strip())
        return True

    finally:
        subprocess.run(["git", "checkout", current_branch], capture_output=True)


def create_investigation_issue(spider_name, filename, classification, evidence, run_history, dry_run=False):
    """Create a GitHub issue for a spider that needs manual investigation."""
    if _existing_pr_or_issue(spider_name):
        return False

    info = FAILURE_EXPLANATIONS[classification]
    evidence_summary = _format_evidence_summary(evidence)
    history_table = _format_run_history_table(run_history, spider_name)

    suggestion_section = ""
    if info["suggestion"]:
        suggestion_section = f"\n### Suggestion\n{info['suggestion']}\n"

    issue_body = f"""## {info["title"]}

{info["explanation"]}

Spider `{spider_name}` (`{filename}`) has produced **0 results for {len(run_history)} consecutive runs**.
{suggestion_section}
### Evidence from latest run
{evidence_summary}

### Run history
{history_table}
"""

    if dry_run:
        logger.info("[DRY RUN] Would create issue for %s (%s)", spider_name, classification.value)
        return True

    result = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "--title",
            f"Dead spider: `{spider_name}` — {info['title']}",
            "--body",
            issue_body,
            "--label",
            "automated:dead-spider-investigation",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Failed to create issue for %s: %s", spider_name, result.stderr)
        return False

    logger.info("Created issue for %s: %s", spider_name, result.stdout.strip())
    return True


def main():
    parser = argparse.ArgumentParser(description="Dead Spider Killer - find and remove broken spiders")
    parser.add_argument(
        "--weeks", type=int, default=5, help="Number of consecutive zero-result runs required (default: 5)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print report without creating PRs or issues")
    parser.add_argument("--max-prs", type=int, default=5, help="Max removal PRs to create per run (default: 5)")
    parser.add_argument(
        "--max-issues", type=int, default=10, help="Max investigation issues to create per run (default: 10)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Step 1: Fetch recent runs
    runs = fetch_recent_runs(args.weeks)
    if len(runs) < args.weeks:
        logger.warning("Only %d runs available, need %d. Proceeding with what we have.", len(runs), args.weeks)

    # Step 2: Find consistently dead spiders
    dead_spiders = find_dead_spiders(runs)
    if not dead_spiders:
        logger.info("No consistently dead spiders found.")
        return 0

    # Step 3: Filter out protected spiders and classify failures
    latest_run_id = runs[-1]["run_id"]
    classified = []

    for spider_name, data in sorted(dead_spiders.items()):
        if has_skip_flag(data["filename"]):
            logger.info("Skipping %s (has skip_auto_delete flag)", spider_name)
            continue

        classification, evidence = classify_failure(spider_name, data["filename"], latest_run_id)
        classified.append((spider_name, data, classification, evidence))

    # Step 4: Summarize
    by_type = {}
    for spider_name, data, classification, evidence in classified:
        by_type.setdefault(classification, []).append(spider_name)

    logger.info("Classification summary:")
    for ftype, spiders in sorted(by_type.items(), key=lambda x: x[0].value):
        action = "REMOVE" if ftype in PR_FAILURES else "ISSUE" if ftype in ISSUE_FAILURES else "SKIP"
        logger.info("  %s (%s): %d spiders", ftype.value, action, len(spiders))
        if args.verbose:
            for s in spiders:
                logger.debug("    - %s", s)

    # Step 5: Create PRs and issues with separate limits
    prs_created = 0
    issues_created = 0

    # Removal PRs for clear failures
    for spider_name, data, classification, evidence in classified:
        if prs_created >= args.max_prs:
            logger.info("Reached PR limit of %d, stopping PRs.", args.max_prs)
            break
        if classification not in PR_FAILURES:
            continue

        if create_removal_pr(
            spider_name, data["filename"], classification, evidence, data["run_history"], dry_run=args.dry_run
        ):
            prs_created += 1

    # Investigation issues for ambiguous cases
    for spider_name, data, classification, evidence in classified:
        if issues_created >= args.max_issues:
            logger.info("Reached issue limit of %d, stopping issues.", args.max_issues)
            break
        if classification not in ISSUE_FAILURES:
            continue

        if create_investigation_issue(
            spider_name, data["filename"], classification, evidence, data["run_history"], dry_run=args.dry_run
        ):
            issues_created += 1

    logger.info("Done. %d PRs created, %d issues created.", prs_created, issues_created)
    return 0


if __name__ == "__main__":
    sys.exit(main())
