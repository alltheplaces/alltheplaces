import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# A house number at the start of the street, e.g. "7555 Falconridge Boulevard
# NE", where the address "number" is then the unit. Calgary also has numbered
# streets such as "8 Avenue SE", which are not house numbers. Street names
# beginning with a number, as in "12 Mile Coulee Road NW", would be split
# wrongly, but no location is on one.
STREET_TYPES = r"Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Way|Passage|Link|Centre|Court|Crescent"
HOUSENUMBER_IN_STREET_REGEX = re.compile(rf"(\d+)\s+(?!(?:{STREET_TYPES})\b)(.+)")
POSTCODE_REGEX = re.compile(r"([A-Z]\d[A-Z])\s*(\d[A-Z]\d)")


class CalgaryPublicLibraryCASpider(BiblioCommonsSpider):
    name = "calgary_public_library_ca"
    item_attributes = {"operator": "Calgary Public Library", "operator_wikidata": "Q5019701"}
    library_id = "calgary"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Locations are named e.g. "Bowness Library", except the prototype
        # branch "Prototype: Skyview".
        if (branch := item["name"].removesuffix(" Library")) != item["name"]:
            item["branch"] = branch

        if item.get("housenumber") and (m := HOUSENUMBER_IN_STREET_REGEX.fullmatch(item.get("street") or "")):
            item["unit"], item["housenumber"], item["street"] = item["housenumber"], m.group(1), m.group(2)
        if postcode := item.get("postcode"):
            item["postcode"] = POSTCODE_REGEX.sub(r"\1 \2", postcode)

        if item["name"] == "Rocky Ridge Library":
            # Inside the YMCA, whose opening hours the library shares.
            item["located_in"] = "Shane Homes YMCA at Rocky Ridge"

        apply_category(Categories.LIBRARY, item)

        yield item
