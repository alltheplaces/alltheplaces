from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SushiExpressTW(Spider):
    name = "sushi_express_tw"
    item_attributes = {"brand": "Sushi Express", "brand_wikidata": "Q15920674"}
    start_urls = ["https://www.sushiexpress.com.tw/WCF/getSpot.ashx"]

    def parse(self, response):
        stores = response.json()
        for store in stores:
            item = DictParser.parse(store)
            item["state"] = store.get("District")
            item["fax"] = store.get("faxNumber")
            self.parse_opening_hours(item, store.get("openingHours"))

            yield item

    def parse_opening_hours(self, item, hours):
        try:
            item["opening_hours"] = OpeningHours()
            hours = hours.split("(")[0]

        except Exception:
            self.crawler.stats.inc_value("failed_hours_parse")
