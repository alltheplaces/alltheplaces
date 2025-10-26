#!/usr/bin/env python3
"""
Script to remove requires_proxy from random spiders.
This helps test if the proxy is actually needed for those spiders.
"""

import os
import random
import re
import subprocess
import sys
from pathlib import Path


def find_spiders_with_requires_proxy():
    """Find all spider files that have requires_proxy defined."""
    spiders_dir = Path(__file__).parent.parent / "locations" / "spiders"
    spiders_with_proxy = []

    for spider_file in spiders_dir.glob("*.py"):
        if spider_file.name.startswith("__"):
            continue

        with open(spider_file, "r") as f:
            content = f.read()

        # Look for requires_proxy = True or requires_proxy = "something"
        if re.search(r'requires_proxy\s*=\s*(?:True|"[^"]*"|\'[^\']*\')', content):
            spiders_with_proxy.append(spider_file)

    return spiders_with_proxy


def remove_requires_proxy_from_spider(spider_file):
    """Remove the requires_proxy line from a spider file."""
    with open(spider_file, "r") as f:
        lines = f.readlines()

    # Find and remove the requires_proxy line
    new_lines = []
    for line in lines:
        # Check if this line contains requires_proxy
        if re.search(r'requires_proxy\s*=\s*(?:True|"[^"]*"|\'[^\']*\')', line):
            # Skip this line entirely (removes the whole line)
            continue
        new_lines.append(line)

    with open(spider_file, "w") as f:
        f.writelines(new_lines)


def create_pull_request(spiders_to_update):
    """Create a pull request with the changes."""
    # Generate a unique branch name with random suffix
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    branch_name = f"remove-requires-proxy-test-{random_suffix}"
    spider_names = [spider.stem for spider in spiders_to_update]

    # Create a new branch
    subprocess.run(
        ["git", "checkout", "-b", branch_name],
        check=True,
    )

    # Stage the changes
    for spider in spiders_to_update:
        subprocess.run(["git", "add", str(spider)], check=True)

    # Create the commit
    spider_list = ", ".join(spider_names)
    commit_message = f"Test removing requires_proxy from: {spider_list}"
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Push the branch
    subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

    # Create pull request using GitHub CLI
    pr_title = f"Test removing requires_proxy from {len(spiders_to_update)} spiders"
    pr_body = f"""This PR tests whether the proxy is actually needed for these spiders:
- {chr(10).join(spider_names)}

The existing CI will run these spiders to check if they still work without the proxy.
If they do, we can merge this PR to save on proxy costs.

Created by remove_requires_proxy.py"""

    # First check if gh command exists
    check_gh = subprocess.run(["which", "gh"], capture_output=True)
    if check_gh.returncode != 0:
        print("Warning: GitHub CLI (gh) not found. PR will need to be created manually.", file=sys.stderr)
        print(f"Branch created: {branch_name}")
        print(f"PR Title: {pr_title}")
        print(f"PR Body:\n{pr_body}")
        return True

    result = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            pr_title,
            "--body",
            pr_body,
            "--base",
            "master",
            "--head",
            branch_name,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Failed to create PR: {result.stderr}", file=sys.stderr)
        return False

    print(f"Created PR: {result.stdout}")
    return True


def main():
    # Get configuration from environment variables (set by GitHub Actions inputs)
    try:
        num_to_select = int(os.getenv('NUM_SPIDERS', '2'))
    except ValueError:
        num_to_select = 2

    # Find spiders with requires_proxy
    spiders = find_spiders_with_requires_proxy()

    if not spiders:
        print("No spiders with requires_proxy found")
        return 0

    print(f"Found {len(spiders)} spiders with requires_proxy")

    # Pick random spiders
    num_to_select = min(num_to_select, len(spiders))
    selected_spiders = random.sample(spiders, num_to_select)

    print(f"Selected {num_to_select} random spiders:")
    for spider in selected_spiders:
        print(f"  - {spider.name}")

    # Remove requires_proxy from selected spiders
    for spider in selected_spiders:
        print(f"Removing requires_proxy from {spider.name}...")
        remove_requires_proxy_from_spider(spider)

    # Create pull request
    if create_pull_request(selected_spiders):
        print("Successfully created pull request")
        return 0
    else:
        print("Failed to create pull request", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
