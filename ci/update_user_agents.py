#!/usr/bin/env python3
"""
Refresh the pinned browser user agent strings in locations/user_agents.py
using real-world data from https://www.useragents.me/.

Only ever moves a pinned version forward (never downgrades it), since the
source site's snapshot can lag behind what is already pinned.
"""

import re
import sys
from pathlib import Path

import requests
from parsel import Selector

USER_AGENTS_PATH = Path(__file__).parent.parent / "locations" / "user_agents.py"
SOURCE_URL = "https://www.useragents.me/"

# The "Latest Linux Desktop Useragents" table lists browsers by OS in the same
# style (X11; Linux x86_64) already pinned in user_agents.py. Firefox usually
# appears at two distinct versions there: the current stable release, and a
# noticeably older one that lines up with the current Firefox ESR release.
LINUX_TABLE_HEADING_ID = "latest-linux-desktop-useragents"

LABEL_RE = re.compile(r"^(Chrome|Firefox)\s+(\d+)")

# The existing pinned strings are a plain, distro-less 64-bit Linux UA. The
# source site lists several Linux flavours (generic, Ubuntu, Fedora, i686)
# per version; prefer a matching plain "X11; Linux x86_64" string, falling
# back to any 64-bit variant, so we don't end up pinning a 32-bit UA.
GENERIC_LINUX_X64_RE = re.compile(r"\(X11; Linux x86_64[;)]")
X64_RE = re.compile(r"x86_64")


def _linux_variant_rank(ua: str) -> int:
    if GENERIC_LINUX_X64_RE.search(ua):
        return 0
    if X64_RE.search(ua):
        return 1
    return 2


FETCH_USER_AGENT = (
    "AllThePlacesBot (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) python-requests"
)


def fetch_linux_user_agents() -> dict[str, list[tuple[int, str]]]:
    resp = requests.get(SOURCE_URL, headers={"User-Agent": FETCH_USER_AGENT}, timeout=30)
    resp.raise_for_status()

    selector = Selector(text=resp.text)
    rows = selector.xpath(
        f'//h2[@id="{LINUX_TABLE_HEADING_ID}"]'
        '/following-sibling::div[contains(@class, "table-responsive")][1]'
        "//tbody/tr"
    )
    if not rows:
        raise RuntimeError(f"Could not find any rows under #{LINUX_TABLE_HEADING_ID} on {SOURCE_URL}")

    candidates: dict[tuple[str, int], list[str]] = {}
    for row in rows:
        label = " ".join(row.xpath("./td[1]//text()").getall()).strip()
        ua = row.xpath(".//textarea/text()").get()
        if not label or not ua:
            continue
        match = LABEL_RE.match(label)
        if not match:
            continue
        browser, major = match.group(1), int(match.group(2))
        candidates.setdefault((browser, major), []).append(ua.strip())

    by_browser: dict[str, list[tuple[int, str]]] = {"Chrome": [], "Firefox": []}
    for (browser, major), uas in candidates.items():
        best = min(uas, key=_linux_variant_rank)
        by_browser[browser].append((major, best))

    return by_browser


def pick_latest_and_esr(
    firefox_versions: list[tuple[int, str]],
) -> tuple[tuple[int, str] | None, tuple[int, str] | None]:
    distinct = sorted(set(firefox_versions), key=lambda v: v[0], reverse=True)
    if not distinct:
        return None, None
    latest = distinct[0]
    esr = None
    for major, ua in distinct[1:]:
        # ESR tracks lag well behind stable; a handful of versions apart is
        # the expected gap, not noise from two nearby point releases.
        if latest[0] - major >= 3:
            esr = (major, ua)
            break
    return latest, esr


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
    by_browser = fetch_linux_user_agents()

    chrome_latest = max(by_browser["Chrome"], key=lambda v: v[0], default=None)
    firefox_latest, firefox_esr = pick_latest_and_esr(by_browser["Firefox"])

    content = USER_AGENTS_PATH.read_text()
    changes = []

    if chrome_latest:
        content, changed = replace_constant_block(content, "CHROME", "CHROME_LATEST", *chrome_latest)
        if changed:
            changes.append(f"Chrome -> {chrome_latest[0]}")

    if firefox_latest:
        content, changed = replace_constant_block(content, "FIREFOX", "FIREFOX_LATEST", *firefox_latest)
        if changed:
            changes.append(f"Firefox -> {firefox_latest[0]}")

    if firefox_esr:
        content, changed = replace_constant_block(content, "FIREFOX_ESR", "FIREFOX_ESR_LATEST", *firefox_esr)
        if changed:
            changes.append(f"Firefox ESR -> {firefox_esr[0]}")
    else:
        print("Could not identify a distinct Firefox ESR version this run; leaving FIREFOX_ESR_LATEST untouched.")

    if not changes:
        print("No user agent constants needed updating.")
        return 0

    USER_AGENTS_PATH.write_text(content)
    print("Updated: " + ", ".join(changes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
