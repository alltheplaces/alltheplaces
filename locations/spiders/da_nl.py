import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class DaNLSpider(scrapy.Spider):
    name = "da_nl"
    start_urls = ["https://www.da.nl/rd/pickup/index"]

    item_attributes = {"brand": "DA Drogisterij", "brand_wikidata": "Q4899756"}

    def parse(self, response, **kwargs):
        for store in response.json().get("stores"):
            oh = OpeningHours()
            for day, hours in store["openinghours"].items():
                if not hours:
                    continue
                for hour in hours.split(" &amp; "):
                    open, close = hour.split("-")
                    oh.add_range(day=sanitise_day(day), open_time=open, close_time=close)
            item = DictParser.parse(store)
            item["lat"] = store["store_latitude"]
            item["lon"] = store["store_longitude"]
            item["phone"] = store["store_phone"]
            item["opening_hours"] = oh
            item["street_address"] = store["address"]
            yield item
