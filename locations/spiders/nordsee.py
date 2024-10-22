from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NordseeSpider(Spider):
    name = "nordsee"
    item_attributes = {"brand": "Nordsee", "brand_wikidata": "Q74866"}
    allowed_domains = ["www.nordsee.com"]
    start_urls = ["https://www.nordsee.com/en/?type=2001"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["uid"]
            item["street_address"] = item.pop("housenumber", None)
            item["opening_hours"] = OpeningHours()
            for day_abbrev, hours_range in location.get("opening").items():
                if isinstance(hours_range, str) and "------" not in hours_range:
                    item["opening_hours"].add_range(day_abbrev.title(), *hours_range.split(" - ", 1), "%H:%M")
            item["website"] = (
                "https://www.nordsee.com"
                + Selector(text=location["listItem"]).xpath('//a[@class="storeListItem__link"]/@href').get()
            )
            yield item
