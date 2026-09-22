from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class HennepinCountyLibraryUSSpider(BiblioCommonsSpider):
    name = "hennepin_county_library_us"
    item_attributes = {"operator": "Hennepin County Library", "operator_wikidata": "Q530512"}
    library_id = "hclib"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # Most cities carry a trailing comma, e.g. "Edina,".
        address = location.get("address") or {}
        for key, value in address.items():
            if isinstance(value, str):
                address[key] = value.strip(" ,")

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Southdale is listed as "Southdale/Yorktown (Hold Pickup only)" while closed for renovation.
        if location.get("id") == "SD":
            item["name"] = "Southdale"
        item["branch"] = item.pop("name")
        item["name"] = "{} Library".format(item["branch"])

        apply_category(Categories.LIBRARY, item)

        yield item
