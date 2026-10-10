import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

POSTCODE_REGEX = re.compile(r"\d{5}(?:-\d{4})?")


class StJosephCountyPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "st_joseph_county_public_library_us"
    item_attributes = {"operator": "St. Joseph County Public Library", "operator_wikidata": "Q69475167"}
    library_id = "sjcpl"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        address = location.get("address") or {}
        # The Tutt Branch has a note appended: "46613 At this address".
        if m := POSTCODE_REGEX.match(address.get("zip") or ""):
            address["zip"] = m.group(0)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # e.g. "Centre Twp Branch", "N. Liberty Branch".
        branch = item.pop("name").removesuffix(" Branch").replace(" Twp", " Township").replace("N. ", "North ")
        item["branch"] = branch
        # The Main Library is the system's headquarters and carries its name.
        item["name"] = self.item_attributes["operator"] if branch == "Main Library" else f"{branch} Branch Library"

        apply_category(Categories.LIBRARY, item)

        yield item
