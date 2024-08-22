import json
from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class BlueBeaconUSSpider(Spider):
    name = "blue_beacon_us"
    item_attributes = {"brand": "Blue Beacon", "brand_wikidata": "Q127435120"}
    start_urls = ["https://bluebeacon.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//script[contains(text(), "directory-map")]/text()').re_first(r"(\[{.+}\]),")
        ):
            item = Feature()
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]

            sel = Selector(text=location["content"])
            item["ref"] = item["website"] = sel.xpath("//a/@href").get()
            item["branch"] = sel.xpath("//a/@title").get()
            item["addr_full"] = sel.xpath('//span[contains(@class, "address")]/text()').get()

            apply_category(Categories.CAR_WASH, item)

            yield item
