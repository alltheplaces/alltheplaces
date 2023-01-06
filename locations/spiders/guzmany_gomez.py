import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.costacoffee_gb import yes_or_no


class GuzmanyGomezSpider(scrapy.Spider):
    name = "guzmany_gomez"
    item_attributes = {"brand": "Guzman y Gomez", "brand_wikidata": "Q23019759"}
    start_urls = ["https://api-external.prod.apps.gyg.com.au/prod/store"]

    def parse(self, response):
        for data in response.json():
            data["street_address"] = ", ".join(filter(None, [data["address1"], data["address2"]]))
            item = DictParser.parse(data)
            oh = OpeningHours()
            for day in data["tradingHours"]:
                for period in day["timePeriods"]:
                    oh.add_range(
                        day=day["dayOfWeek"],
                        open_time=period["openTime"],
                        close_time=period["endTime"],
                    )
            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = data["orderLink"]
            item["extras"] = {
                "wheelchair": yes_or_no(any("Wheelchair accessible" == t["tag"] for t in data["tags"])),
                "sells:alcohol": yes_or_no(any("Liquor" == t["tag"] for t in data["tags"])),
            }
            yield item
