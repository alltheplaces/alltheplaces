import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.communico import CommunicoSpider

BRANCH_URL = "https://www.theoceancountylibrary.org/Branches/{}.htm"
# No location has an "about_url". Paths checked against theoceancountylibrary.org.
BRANCH_PAGES = {
    "1877": "TR/tr",
    "1884": "BGT/bgt",
    "1885": "BH/bh",
    "1886": "BD/bd",
    "1888": "BKY/bky",
    "1889": "B/b",
    "1890": "IH/ih",
    "1891": "JA/ja",
    "1892": "LA/la",
    "1893": "LAK/lak",
    "1894": "LEH/leh",
    "1895": "LBI/lbi",
    "1896": "MA/ma",
    "1897": "PL/pl",
    "1898": "P/p",
    "1899": "STF/stf",
    "1900": "T/t",
    "1901": "UP/up",
    "1902": "WA/wa",
    "1903": "WH/wh",
    "1904": "PX/px",
}
PO_BOX_REGEX = re.compile(r"^P\.?\s*O\.?\s*Box\b", re.IGNORECASE)


class OceanCountyLibraryUSSpider(CommunicoSpider):
    name = "ocean_county_library_us"
    item_attributes = {"operator": "Ocean County Library", "operator_wikidata": "Q7075971"}
    communico_client = "theoceancountylibrary"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        line2 = (location.get("line2") or "").strip()
        if line2.casefold() == (location.get("locality") or "").strip().casefold() or PO_BOX_REGEX.match(line2):
            # Point Pleasant Borough repeats its city as a second address line
            # and Island Heights follows its street with a post office box.
            location["line2"] = ""

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if path := BRANCH_PAGES.get(location["id"]):
            item["website"] = BRANCH_URL.format(path)

        apply_category(Categories.LIBRARY, item)

        yield item
