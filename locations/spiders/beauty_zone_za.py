from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class BeautyZoneZASpider(Spider):
    name = "beauty_zone_za"
    start_urls = ["https://beautyzone.co.za/store-locator/"]
    item_attributes = {"brand": "Beauty Zone", "brand_wikidata": "Q118185921"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId={}".format(
                response.xpath('//*[@class="LB_StoreLocator"]//@id').get()
            ),
            callback=self.parse_location,
        )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Beauty Zone ")
            item["street_address"] = merge_address_lines([location["addressLine2"], location["addressLine1"]])

            oh = OpeningHours()
            for day_time in location["regularHours"]:
                day = day_time["openDay"]
                if day != "PUBLIC":
                    oh.add_range(day, day_time["openTime"], day_time["closeTime"])
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_COSMETICS, item)

            yield item
