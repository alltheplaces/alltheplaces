import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

BRANCH_SUFFIX_REGEX = re.compile(r"\s+Branch$")


class FultonCountyLibrarySystemUSSpider(BiblioCommonsSpider):
    name = "fulton_county_library_system_us"
    item_attributes = {"operator": "Fulton County Library System", "operator_wikidata": "Q4815975"}
    library_id = "fulcolibrary"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        label = item.pop("name").replace(" @ ", " at ")
        if BRANCH_SUFFIX_REGEX.search(label):
            item["branch"] = BRANCH_SUFFIX_REGEX.sub("", label)
            item["name"] = "{} Library".format(item["branch"])
        else:
            item["name"] = label

        apply_category(Categories.LIBRARY, item)

        yield item
