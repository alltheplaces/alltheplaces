import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

HOUSENUMBER_REGEX = re.compile(r"(\d+\S*)\s+(.+)")


class BostonPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "boston_public_library_us"
    item_attributes = {"operator": "Boston Public Library", "operator_wikidata": "Q894583"}
    library_id = "bpl"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        address = location.get("address") or {}
        if not (address.get("number") or "").strip()[:1].isdigit():
            # The Chinatown branch has its full name in "number" and the
            # house number at the start of "street".
            address["number"] = None
            if m := HOUSENUMBER_REGEX.fullmatch((address.get("street") or "").strip()):
                address["number"], address["street"] = m.group(1), m.group(2)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch == "Central Library in Copley Square":
            item["branch"] = "Central Library"
            item["name"] = "Boston Public Library"
        else:
            item["branch"] = branch
            item["name"] = "{} Branch Library".format(branch)

        apply_category(Categories.LIBRARY, item)

        yield item
