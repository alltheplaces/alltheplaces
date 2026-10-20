from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class StTammanyParishLibraryUSSpider(BiblioCommonsSpider):
    name = "st_tammany_parish_library_us"
    item_attributes = {"operator": "St. Tammany Parish Library", "operator_wikidata": "Q69477262"}
    library_id = "stpl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Every location is named "<Branch> Branch", e.g. "Lee Road Branch".
        item["branch"] = item.pop("name").removesuffix(" Branch")
        item["name"] = "{} Library".format(item["branch"])

        apply_category(Categories.LIBRARY, item)

        yield item
