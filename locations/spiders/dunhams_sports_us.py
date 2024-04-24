import re

from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DunhamsSportsUSSpider(Spider):
    name = "dunhams_sports_us"
    item_attributes = {"brand": "Dunham's Sports", "brand_wikidata": "Q5315238"}
    allowed_domains = ["www.dunhamssports.com"]
    start_urls = [
        "https://www.dunhamssports.com/on/demandware.store/Sites-dunhamssports-Site/en_US/Stores-FindStores?showMap=true&radius=4000&lat=36.0711&long=-86.7196"
    ]

    def parse(self, response):
        for location in response.json().get("stores"):
            item = DictParser.parse(location)
            if location.get("ID"):
                item["website"] = "https://www.dunhamssports.com/store-details?storeID={}".format(location.get("ID"))
            hours_text = re.sub(
                r"\s+",
                " ",
                " ".join(filter(None, Selector(text=location.get("storeHours", "")).xpath("//td/text()").getall())),
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)
            yield item
