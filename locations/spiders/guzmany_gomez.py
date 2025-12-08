import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class GuzmanyGomezSpider(scrapy.Spider):
    name = "guzmany_gomez"
    item_attributes = {"brand": "Guzman y Gomez", "brand_wikidata": "Q23019759"}
    start_urls = ["https://api-external.prod.apps.gyg.com.au/prod/store"]

    def parse(self, response):
        for data in response.json():
            data["street_address"] = clean_address([data["address1"], data["address2"]])
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
            apply_yes_no(Extras.WHEELCHAIR, item, any("Wheelchair accessible" == t["tag"] for t in data["tags"]), False)
            apply_yes_no("sells:alcohol", item, any("Liquor" == t["tag"] for t in data["tags"]), False)
            yield item
