import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GuzmanyGomezSpider(scrapy.Spider):
    name = "guzmany_gomez"
    item_attributes = {"brand": "Guzman Y Gomez", "brand_wikidata": "Q23019759"}
    allowed_domains = ["guzmanygomez.com.au"]
    start_urls = ["https://api-external.prod.apps.gyg.com.au/prod/store"]

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)
            oh = OpeningHours()
            for day in data.get("tradingHours"):
                if not day.get("timePeriods"):
                    continue
                oh.add_range(
                    day=day.get("dayOfWeek"),
                    open_time=day.get("timePeriods")[0].get("openTime"),
                    close_time=day.get("timePeriods")[0].get("endTime"),
                )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
