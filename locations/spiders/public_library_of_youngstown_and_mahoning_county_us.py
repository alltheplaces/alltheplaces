from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class PublicLibraryOfYoungstownAndMahoningCountyUSSpider(BiblioCommonsSpider):
    name = "public_library_of_youngstown_and_mahoning_county_us"
    item_attributes = {
        "operator": "Public Library of Youngstown and Mahoning County",
        "operator_wikidata": "Q69487977",
    }
    library_id = "plymc"
    # Every location lists the system's central number.
    drop_attributes = {"phone"}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["name"] = "{} Library".format(item["branch"])
        apply_category(Categories.LIBRARY, item)
        yield item
