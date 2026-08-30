#!/usr/bin/env python3
"""
Refresh the pinned browser user agent strings in locations/user_agents.py
using official version data from Mozilla and Google.

Only ever moves a pinned version forward (never downgrades it), since these
services occasionally serve a staged/rolled-back version.
"""

import re
import sys
from pathlib import Path

import requests

USER_AGENTS_PATH = Path(__file__).parent.parent / "locations" / "user_agents.py"

FIREFOX_VERSIONS_URL = "https://product-details.mozilla.org/1.0/firefox_versions.json"
CHROME_VERSIONS_URL = (
    "https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions/all/releases"
    "?filter=endtime=none"
)

FETCH_USER_AGENT = (
    "AllThePlacesBot (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) python-requests"
)

FIREFOX_UA_TEMPLATE = "Mozilla/5.0 (X11; Linux x86_64; rv:{major}.0) Gecko/20100101 Firefox/{major}.0"
CHROME_UA_TEMPLATE = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
)


def major_version(version: str) -> int:
    return int(re.match(r"\d+", version).group())


def fetch_firefox_majors() -> tuple[int, int]:
    """Returns (latest, esr) major versions."""
    resp = requests.get(FIREFOX_VERSIONS_URL, headers={"User-Agent": FETCH_USER_AGENT}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return major_version(data["LATEST_FIREFOX_VERSION"]), major_version(data["FIREFOX_ESR"])


def fetch_chrome_major() -> int:
    resp = requests.get(CHROME_VERSIONS_URL, headers={"User-Agent": FETCH_USER_AGENT}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    releases = data.get("releases", [])
    if not releases:
        raise RuntimeError(f"No Chrome releases returned from {CHROME_VERSIONS_URL}")
    return major_version(releases[0]["version"])


def current_pinned_version(content: str, constant_prefix: str) -> int | None:
    match = re.search(rf'{constant_prefix}_(\d+) = "', content)
    return int(match.group(1)) if match else None


def replace_constant_block(
    content: str, constant_prefix: str, alias_name: str, new_major: int, new_ua: str
) -> tuple[str, bool]:
    old_major = current_pinned_version(content, constant_prefix)
    if old_major is not None and new_major <= old_major:
        return content, False

    pattern = re.compile(rf'{constant_prefix}_\d+ = "[^"]*"\n{alias_name} = {constant_prefix}_\d+')
    new_block = f'{constant_prefix}_{new_major} = "{new_ua}"\n{alias_name} = {constant_prefix}_{new_major}'
    new_content, count = pattern.subn(new_block, content)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {alias_name} block in {USER_AGENTS_PATH}, found {count}")
    return new_content, True


def main() -> int:
    firefox_latest, firefox_esr = fetch_firefox_majors()
    chrome_latest = fetch_chrome_major()

    content = USER_AGENTS_PATH.read_text()
    changes = []

    content, changed = replace_constant_block(
        content, "CHROME", "CHROME_LATEST", chrome_latest, CHROME_UA_TEMPLATE.format(major=chrome_latest)
    )
    if changed:
        changes.append(f"Chrome -> {chrome_latest}")

    content, changed = replace_constant_block(
        content, "FIREFOX", "FIREFOX_LATEST", firefox_latest, FIREFOX_UA_TEMPLATE.format(major=firefox_latest)
    )
    if changed:
        changes.append(f"Firefox -> {firefox_latest}")

    content, changed = replace_constant_block(
        content, "FIREFOX_ESR", "FIREFOX_ESR_LATEST", firefox_esr, FIREFOX_UA_TEMPLATE.format(major=firefox_esr)
    )
    if changed:
        changes.append(f"Firefox ESR -> {firefox_esr}")

    if not changes:
        print("No user agent constants needed updating.")
        return 0

    USER_AGENTS_PATH.write_text(content)
    print("Updated: " + ", ".join(changes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
