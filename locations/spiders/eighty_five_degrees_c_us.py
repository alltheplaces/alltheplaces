from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class EightyFiveDegreesCUSSpider(WPStoreLocatorSpider):
    name = "eighty_five_degrees_c_us"
    item_attributes = {"brand": "85°C Bakery Cafe", "brand_wikidata": "Q4644852"}
    allowed_domains = ["www.85cbakerycafe.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 24
    max_results = 6
    days = DAYS_EN
    custom_settings = {"RETRY_HTTP_CODES": [508]}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("85°C ")
        item["extras"]["website:orders"] = feature["order_url"]
        del item["website"]

        apply_category(Categories.CAFE, item)

        yield item
