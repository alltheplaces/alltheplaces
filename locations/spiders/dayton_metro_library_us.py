from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class DaytonMetroLibraryUSSpider(BiblioCommonsSpider):
    name = "dayton_metro_library_us"
    item_attributes = {"operator": "Dayton Metro Library", "operator_wikidata": "Q5243554"}
    library_id = "dayton"
    # Every branch lists the system-wide "Ask Me Line" rather than its own number.
    drop_attributes = {"phone"}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        item["branch"] = branch.removesuffix(" Branch").removesuffix(" Library")
        # e.g. "Brookville Branch", signed and mapped as "Brookville Branch Library".
        item["name"] = branch if branch.endswith("Library") else "{} Library".format(branch)
        apply_category(Categories.LIBRARY, item)

        yield item
