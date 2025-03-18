import re

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_DK, NAMED_DAY_RANGES_DK, OpeningHours


class TelenorDKSpider(Spider):
    name = "telenor_dk"
    item_attributes = {"brand": "Telenorbutikken", "brand_wikidata": "Q845632"}
    start_urls = [
        "https://www.telenor.dk/da/sharedblock/2ed9d2b7-45d2-4f7d-9406-a933d6883cdc/FindNearestShopBlock/GetShops/2bd5f376-3f79-475b-aa1e-b45174b9a2f3/"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, headers={"X-Requested-With": "XMLHttpRequest"})

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            html = Selector(text=location["html"])
            item["addr_full"] = re.sub(
                r"\s+", " ", ", ".join(filter(None, html.xpath("//div/div/div[1]/div/p/text()").getall()))
            )
            item["phone"] = html.xpath("//div/div/div[2]/p[1]/text()").get().replace("Telefon:", "").strip()
            item["opening_hours"] = OpeningHours()
            hours_string = " ".join(html.xpath("//div/div/div[3]/div//text()").getall()).strip()
            item["opening_hours"].add_ranges_from_string(
                hours_string, days=DAYS_DK, named_day_ranges=NAMED_DAY_RANGES_DK
            )
            yield item
