import re

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DoroITSpider(WPStoreLocatorSpider):
    name = "doro_it"
    item_attributes = {"brand": "Doro", "brand_wikidata": "Q136464598"}
    allowed_domains = ["www.dorosupermercati.it"]
    iseadgg_countries_list = ["IT"]
    search_radius = 100
    max_results = 100

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> None:
        if "Daily" in item["name"]:
            item["brand"] = "Doro Daily"
            item["brand_wikidata"] = "Q137801479"
        else:
            item["brand"] = "Doro"
            item["brand_wikidata"] = "Q136464598"

        item["branch"] = re.sub(r"^Doro(?:\s+Daily)?\s+", "", item["name"])

        if state := item.get("state"):
            item["state"] = state.strip("()")

        if "Daily" in item["name"]:
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
