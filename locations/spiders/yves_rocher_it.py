import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS


class YvesRocherItSpider(scrapy.Spider):
    name = "yves_rocher_it"
    item_attributes = {
        "brand": "Yves Rocher",
        "brand_wikidata": "Q1477321",
    }
    allowed_domains = ["yves-rocher.it"]
    start_urls = ["https://uberall.com/api/storefinders/HLGRPp968JZaR0D235dXJa5fMRPHuA/locations/all"]

    def parse(self, response):
        for data in response.json().get("response", {}).get("locations"):
            item = DictParser.parse(data)
            item["street_address"] = data.get("streetAndNumber")
            oh = OpeningHours()
            for day in data.get("openingHours"):
                oh.add_range(day=DAYS[day.get("dayOfWeek") - 1], open_time=day.get("from1"), close_time=day.get("to1"))
                if day.get("from2"):
                    oh.add_range(
                        day=DAYS[day.get("dayOfWeek") - 1], open_time=day.get("from2"), close_time=day.get("to2")
                    )

            item["opening_hours"] = oh.as_opening_hours()
            yield item
