import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class HmNLSpider(scrapy.Spider):
    name = "hm_nl"
    item_attributes = {
        "brand": "H&M",
        "brand_wikidata": "Q188326",
    }
    start_urls = [
        "https://api.storelocator.hmgroup.tech/v2/brand/hm/stores/locale/nl_nl/country/NL?_type=json&campaigns=true"
        "&departments=true&openinghours=true&maxnumberofstores=100"
    ]

    def parse(self, response):
        for store in response.json().get("stores"):
            opening_hours = OpeningHours()
            oh = store["openingHours"]

            for day_hour in oh:
                day = sanitise_day(day_hour["name"], DAYS_NL)
                if day is not None:
                    opening_hours.add_range(day=day, open_time=day_hour["opens"], close_time=day_hour["closes"])

            item = DictParser.parse(store)
            item["opening_hours"] = opening_hours
            item["ref"] = store["storeCode"]
            item["name"] = store["name"]
            item["city"] = store["city"]
            item["addr_full"] = store["address"]["streetName1"]
            yield item
