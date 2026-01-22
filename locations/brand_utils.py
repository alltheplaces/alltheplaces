"""
Utilities for extracting brand information from location names and branches.
"""

import re


def extract_located_in(
    name: str, mappings: list, spider=None, match_mode: str = "contains"
) -> tuple[str | None, str | None]:
    """Extract located_in brand and wikidata ID from name using keyword mappings.

    This helper function searches for brand keywords in a location name/branch and
    returns the corresponding brand name and wikidata ID. Commonly used for ATMs
    located within retail stores.

    Uses word boundary matching to avoid false positives (e.g., "PTT" won't match "HTTPTTPS").

    Args:
        name: Name or branch string to search in (case-insensitive matching)
        mappings: List of (keywords, brand_data) or (keywords, brand_data, mode) tuples where:
            - keywords: List of strings to search for in the name
            - brand_data: Dict with "brand"/"name" and "brand_wikidata" keys
            - mode: Optional "contains" or "equals" (default: uses match_mode parameter)
        spider: Optional spider instance for logging unmapped brands
        match_mode: Default matching mode (default: "contains")
            - "contains": Match keyword anywhere in the string with word boundaries
            - "equals": Match only when keyword equals the name (allows suffixes like "Stores", "Express")

    Returns:
        Tuple of (located_in, located_in_wikidata) or (None, None) if no match found

    Examples:
        >>> # Contains mode (default)
        >>> mappings = [
        ...     (["7-11", "7-ELEVEN"], {"brand": "7-Eleven", "brand_wikidata": "Q259340"}),
        ...     (["LOTUS"], {"brand": "Lotus's", "brand_wikidata": "Q2647070"}),
        ... ]
        >>> extract_located_in("ATM at 7-11 Store", mappings, self)
        ('7-Eleven', 'Q259340')
        >>> extract_located_in("HTTPTTPS://example.com", [(["PTT"], {"brand": "PTT"})], self)
        (None, None)  # No false positive

        >>> # Equals mode - keyword must equal the name
        >>> mappings = [(["PREMIER"], {"brand": "Premier", "brand_wikidata": "Q7240340"})]
        >>> extract_located_in("Premier", mappings, self, match_mode="equals")
        ('Premier', 'Q7240340')
        >>> extract_located_in("Premier Stores", mappings, self, match_mode="equals")
        ('Premier', 'Q7240340')
        >>> extract_located_in("WALLSEND PREMIER", mappings, self, match_mode="equals")
        (None, None)  # Doesn't equal "Premier"

        >>> # Mix modes per mapping
        >>> mappings = [
        ...     (["PREMIER"], {"brand": "Premier", "brand_wikidata": "Q7240340"}, "equals"),
        ...     (["WALGREENS"], {"brand": "Walgreens", "brand_wikidata": "Q1591889"}, "contains"),
        ... ]
    """
    name_upper = name.upper().strip()

    for mapping in mappings:
        # Unpack tuple
        if len(mapping) == 3:
            keywords, brand_data, mode = mapping
        else:
            keywords, brand_data = mapping
            mode = match_mode  # Use default

        for keyword in keywords:
            keyword_upper = keyword.upper()

            if mode == "equals":
                # Match only when keyword equals the name
                pattern = r"^" + re.escape(keyword_upper) + r"$"
            else:  # mode == "contains"
                # Match anywhere with word boundaries
                # Uses lookbehind/lookahead to allow non-ASCII characters (Thai, etc.) as boundaries
                # Matches: "TOPS" in "ทีเอ็มบีธนชาตTOPS DAILY" (Thai text + English)
                # Does NOT match: "PTT" in "HTTPTTPS" (embedded in alphanumeric)
                pattern = r"(?:^|(?<=[^A-Z0-9]))" + re.escape(keyword_upper) + r"(?:(?=[^A-Z0-9])|$)"

            if re.search(pattern, name_upper):
                located_in = brand_data.get("brand", brand_data.get("name"))
                located_in_wikidata = brand_data.get("brand_wikidata")

                return located_in, located_in_wikidata

    if spider and name_upper:
        spider.crawler.stats.inc_value(f"atp/located_in_failed/{name_upper}")

    # Don't set located_in properties if they can't be mapped.
    return None, None
