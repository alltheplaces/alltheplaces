from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class YolkUSSpider(StructuredDataSpider):
    name = "yolk_us"
    item_attributes = {"brand": "Yolk", "country": "US"}
    allowed_domains = ["i.eatyolk.com"]
    start_urls = ["https://i.eatyolk.com/locations"]
    wanted_types = ["Restaurant"]
    search_for_email = False
    search_for_twitter = False
    search_for_facebook = False
    search_for_amenity_features = False
    search_for_payment_accepted = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]
        item["name"] = self.item_attributes["brand"]
        item["branch"] = ld_data["name"].removeprefix("Yolk - ").strip()
        item["extras"]["cuisine"] = "american;brunch"
        apply_category(Categories.RESTAURANT, item)
        yield item
