import re
from html import unescape
from typing import Iterable

from scrapy import Selector, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class KiaAUSpider(Spider):
    name = "kia_au"
    item_attributes = {"brand": "Kia", "brand_wikidata": "Q35349", "extras": Categories.SHOP_CAR.value}
    allowed_domains = ["www.kia.com"]
    start_urls = ["https://www.kia.com/api/kia_australia/base/fd01/findDealer.selectFindDealerAllList?isAll=true"]

    def parse(self, response):
        for location in response.json()["dataInfo"]:
            if location["displayYn"] == "N":
                continue  # Dealer is permanently closed.
            if location["delYn"] == "Y":
                continue  # Dealer deleted (probably franchised under a new name/dealer ID).
            item = DictParser.parse(location)
            item["ref"] = location.get("dealerCode", str(location["dealerSeq"]))
            item["name"] = location["dealerNm"]
            if item["website"] and item["website"].startswith("www."):
                item["website"] = "https://" + item["website"]
            if location.get("openHours"):
                hours_text = unescape(
                    re.sub(
                        r"\s+", " ", " ".join(Selector(text=location["openHours"]).xpath("//text()").getall()).strip()
                    )
                )
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_text)
            yield from self.post_process_feature(item, location) or []

    def post_process_feature(self, item: Feature, feature: dict) -> Iterable[Feature]:
        if feature["dealerNm"] == "testtest":
            return
        yield item
