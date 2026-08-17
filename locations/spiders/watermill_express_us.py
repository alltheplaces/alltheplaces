from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, PaymentMethods, Vending, add_vending, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class WatermillExpressUSSpider(WPStoreLocatorSpider):
    name = "watermill_express_us"
    item_attributes = {"brand": "Watermill Express", "brand_wikidata": "Q126195259"}
    allowed_domains = ["watermillexpress.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 500
    max_results = 5000

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name")
        item["branch"] = feature["nickname"]
        item["country"] = "US"
        item["website"] = feature["permalink"]
        item["opening_hours"] = "24/7"

        apply_category(Categories.VENDING_MACHINE, item)
        add_vending(Vending.WATER, item)
        if feature.get("bagged_ice") or feature.get("bulk_ice"):
            add_vending(Vending.ICE_CUBES, item)
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, feature.get("credit_card_reader") == "Yes")

        yield item
