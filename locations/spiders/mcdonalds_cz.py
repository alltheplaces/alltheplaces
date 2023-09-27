import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsCZSpider(scrapy.Spider):
    name = "mcdonalds_cz"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.cz"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "https://restaurace.mcdonalds.cz/api?token=7983978c4175e5a88b9a58e5b5c6d105217fbc625b6c20e9a8eef3b8acc6204f",
    )

    def parse_hours(self, item, poi):
        if worktime := poi.get("worktime"):
            oh = OpeningHours()
            try:
                for day, times in zip(DAYS, worktime):
                    open, close = times.split(" - ")
                    oh.add_range(day, open.strip(), close.strip())
                item["opening_hours"] = oh
            except:
                self.logger.warning(f"Couldn't parse opening hours: {worktime}")

    def parse(self, response):
        pois = response.json().get("restaurants")
        for poi in pois:
            poi["street_address"] = poi.pop("address")
            item = DictParser.parse(poi)
            item["website"] = response.urljoin(poi["slug"])
            item["postcode"] = str(item["postcode"])
            self.parse_hours(item, poi)
            yield item
