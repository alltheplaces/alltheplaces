from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider

# Which Wich runs the Agile Store Locator WordPress plugin, which exposes every
# location in a single admin-ajax.php response.
#
# Note that whichwich.com sits behind Imunify360 bot protection, which rejects
# requests from data centre IP ranges with a 403 and a JSON "Access denied"
# body. The spider works from an ordinary connection.


class WhichWichUSSpider(AgileStoreLocatorSpider):
    name = "which_wich_us"
    item_attributes = {"brand": "Which Wich?", "brand_wikidata": "Q7993556"}
    allowed_domains = ["whichwich.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if (feature.get("country") or "United States") not in ["United States", "USA", "US"]:
            return

        item["branch"] = item.pop("name", None)
        item["ref"] = feature["id"]

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"

        yield item
