from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class BeautyZoneZASpider(Spider):
    name = "beauty_zone_za"
    start_urls = ["https://beautyzone.co.za/store-locator/"]
    item_attributes = {
        "brand": "Beauty Zone",
        "brand_wikidata": "Q118185921",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        client_id = response.xpath('//*[@class="LB_StoreLocator"]//@id').get()
        yield JsonRequest(
            url=f"https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId={client_id}",
            callback=self.parse_location,
        )

    def parse_location(self, response, **kwargs):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["addressLine2"], location["addressLine1"]])
            oh = OpeningHours()
            for day_time in location["regularHours"]:
                day = day_time["openDay"]
                if day != "PUBLIC":
                    open_time = day_time["openTime"]
                    close_time = day_time["closeTime"]
                    oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
            yield item
