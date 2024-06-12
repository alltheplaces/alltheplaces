from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SushiExpressTW(Spider):
    name = "sushi_express_tw"
    item_attributes = {"brand": "Sushi Express", "brand_wikidata": "Q15920674"}
    start_urls = ["https://www.sushiexpress.com.tw/WCF/getSpot.ashx"]

    def parse(self, response):
        stores = response.json()
        for store in stores:
            item = DictParser.parse(store)
            item["state"] = store.get("district")
            item["extras"]["fax"] = store.get("faxNumber")
            self.parse_opening_hours(item, store.get("openingHours"))

            yield item

    def parse_opening_hours(self, item, full_hours):
        try:
            full_hours = full_hours.replace("~", "-")
            item["opening_hours"] = OpeningHours()
            hours = full_hours.split("（")[0]  # Has weird character in string. Shows hours and last order hour?
            item["opening_hours"].add_days_range(DAYS, hours.split("-")[0], hours.split("-")[1])

        except Exception:
            self.crawler.stats.inc_value("failed_hours_parse")
