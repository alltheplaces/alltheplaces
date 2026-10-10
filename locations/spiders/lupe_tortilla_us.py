from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider

# Lupe Tortilla runs the Agile Store Locator WordPress plugin, which returns
# every restaurant in one admin-ajax.php response. Its records spell the state
# out, which the project's state clean up pipeline normalises.


class LupeTortillaUSSpider(AgileStoreLocatorSpider):
    name = "lupe_tortilla_us"
    item_attributes = {"brand": "Lupe Tortilla", "brand_wikidata": "Q126346007"}
    allowed_domains = ["tex-mex.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name", None)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "tex-mex"

        yield item
