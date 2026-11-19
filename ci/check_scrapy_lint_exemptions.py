"""Quick check if a newly modified file has scrapy-lint exemptions that should be removed"""

# Since this script is a shim that won't last forever, it is not following best practices; e.g. cannot be imported elsewhere

import sys
import tomllib
from typing import Final

try:
    # Parse the TOML file:
    with open("pyproject.toml", "rb") as config_file:
        full_config: Final = tomllib.load(config_file)

    exemptions: Final = full_config["tool"]["scrapy-lint"]["per-file-ignores"]
    allowed: Final[set[str]] = set(full_config["tool"].get("scrapy-lint-exemptions", {}))

except Exception:
    import logging

    logging.exception("Could not parse exemptions")  # noqa: LOG015
    sys.exit(0)

# Quickest way to find matches would be make them each a set and get intersection:
matches: Final[set[str]] = (set(sys.argv) & set(exemptions)) - allowed
for match in sorted(matches):
    print(  # noqa: T201
        f"WARNING: {match} has exemption(s) {exemptions[match]} in pyproject.toml that should be fixed and exemption removed"
    )
# CI calls with --all-files so the warnings on the screen will need to be enough :/
# sys.exit(bool(matches))
