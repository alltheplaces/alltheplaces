import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

HOUSENUMBER_REGEX = re.compile(r"(\d+\S*)\s+(.+)")

NON_BRANCH_IDS = {
    "HCPL",  # Administrative offices, "not a library branch" by its own description.
    "OUT",  # Community Outreach, an outreach service listed at "Various locations".
    "LAW",  # Harris County Law Library, a separate county law library HCPL delivers holds to.
    "TMC",  # The TMC Library, an independent medical library HCPL delivers holds to.
}


class HarrisCountyPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "harris_county_public_library_us"
    item_attributes = {"operator": "Harris County Public Library", "operator_wikidata": "Q5836595"}
    library_id = "hcpl"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # Some branches have the house number at the start of the street
        # rather than in "number", e.g. "22248 Aldine Westfield Road".
        address = location.get("address") or {}
        if not address.get("number") and (m := HOUSENUMBER_REGEX.fullmatch((address.get("street") or "").strip())):
            address["number"], address["street"] = m.group(1), m.group(2)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if location.get("id") in NON_BRANCH_IDS:
            return

        apply_category(Categories.LIBRARY, item)

        yield item
