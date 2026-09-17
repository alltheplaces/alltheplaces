from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.storefinders.bibliocommons import BiblioCommonsSpider


class KingCountyLibrarySystemUSSpider(BiblioCommonsSpider):
    name = "king_county_library_system_us"
    item_attributes = {"operator": "King County Library System", "operator_wikidata": "Q6411390"}
    library_id = "kcls"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if branch := item.get("branch"):  # Lockers have a name instead.
            if branch.startswith("Administrative Office"):
                # Administration building, not a library branch.
                return

            # e.g. "Kent Closed. Holds Pickup at Kent Panther Lake."
            # (temporarily closed for renovation)
            branch = item["branch"] = branch.split(" Closed.", 1)[0]
            item["name"] = branch if "Library" in branch else "{} Library".format(branch)

        yield item
