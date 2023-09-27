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
                i = 0
                for day in worktime:
                    open, close = day.split(" - ")
                    oh.add_range(DAYS[i], open.strip(), close.strip())
                    i += 1
                item["opening_hours"] = oh.as_opening_hours()
            except:
                self.logger.warning(f"Couldn't parse opening hours: {worktime}")

    def parse(self, response):
        pois = response.json().get("restaurants")
        for poi in pois:
            poi['street_address'] = poi.pop('address')
            item = DictParser.parse(poi)
            item["postcode"] = str(item["postcode"])
            self.parse_hours(item, poi)
            yield item
