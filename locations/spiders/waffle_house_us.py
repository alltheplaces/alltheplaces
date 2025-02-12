import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class WaffleHouseUSSpider(Spider):
    name = "waffle_house_us"
    item_attributes = {"brand": "Waffle House", "brand_wikidata": "Q1701206"}
    allowed_domains = ["wafflehouse.com"]
    start_urls = ["https://locations.wafflehouse.com/regions"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations_text = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        locations = json.loads(locations_text)["props"]["pageProps"]["locations"]
        for location in locations:
            item = DictParser.parse(location)
            item["name"] = item["name"].removesuffix(" #{}".format(location["storeCode"]))
            item["ref"] = location["storeCode"]
            item["street_address"] = clean_address(location["addressLines"])
            item["phone"] = "; ".join(location["phoneNumbers"])
            item["website"] = "https://locations.wafflehouse.com/{}/".format(location["slug"])
            item["extras"]["website:orders"] = location["custom"].get("online_order_link")
            item["operator"] = location["custom"]["operated_by"]

            try:
                item["opening_hours"] = self.parse_opening_hours(location["businessHours"] or [])
            except:
                self.logger.error("Error parsing opening hours: {}".format(location["businessHours"]))

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for day, times in zip(DAYS, rules):
            if not times:
                oh.set_closed(day)
            else:
                oh.add_range(day, times[0], times[1].replace("00:00", "24:00"))
        return oh
