from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class ColumbusMetropolitanLibraryUSSpider(BiblioCommonsSpider):
    name = "columbus_metropolitan_library_us"
    item_attributes = {"operator": "Columbus Metropolitan Library", "operator_wikidata": "Q5150078"}
    library_id = "cml"
    # Every location lists the same number, the system-wide main line.
    drop_attributes = {"phone"}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = branch = item.pop("name")
        item["name"] = (
            "Columbus Metropolitan Library" if branch == "Main Library" else "{} Branch Library".format(branch)
        )

        apply_category(Categories.LIBRARY, item)

        yield item
