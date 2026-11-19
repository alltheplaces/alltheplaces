"""Quick check if a newly modified file has scrapy-lint exemptions that should be removed"""

import sys
import tomllib
from typing import Final


def parse_toml() -> list[str]:
    """Parses toml config"""
    # This is wrapped in a function to avoid sys.exit call unless called
    try:
        with open("pyproject.toml", "rb") as config_file:
            config = tomllib.load(config_file)
            exemptions: Final = config["tool"]["scrapy-lint"]["per-file-ignores"]
    except Exception:
        import logging

        logging.exception("Could not parse exemptions")  # noqa: LOG015
        sys.exit(0)
    return exemptions


def main(argv: list[str]) -> None:
    exemptions: Final = parse_toml()
    # Quickest way to find matches would be make them each a set and get intersection:
    matches: Final[set[str]] = set(argv) & set(exemptions)
    for match in matches:
        print(f"{match} has an exemption in pyproject.toml that needs to be fixed and removed")  # noqa: T201
    sys.exit(bool(matches))


if __name__ == "__main__":
    main(sys.argv)
