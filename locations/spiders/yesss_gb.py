from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class YesssGBSpider(Spider):
    name = "yesss_gb"
    item_attributes = {"brand": "Yesss Electrical", "brand_wikidata": "Q91307483"}
    start_urls = ["https://www.yesss.co.uk/store-finder/location-data/all"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = LinkedDataParser.parse_ld(location["ldSchema"])
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["email"] = location["email"]
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_ELECTRICAL, item)

            # The feed's hours are a 00:00-00:00 placeholder; the real hours are on each store page
            yield Request(location["url"], callback=self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        if ld := LinkedDataParser.find_linked_data(response, "WholesaleStore"):
            item["opening_hours"] = LinkedDataParser.parse_opening_hours(ld)

        yield item
