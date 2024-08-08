import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_SE, OpeningHours, sanitise_day


class HemkopSESpider(scrapy.Spider):
    name = "hemkop_se"
    item_attributes = {"brand": "Hemköp", "brand_wikidata": "Q10521746"}
    start_urls = ["https://www.hemkop.se/axfood/rest/search/store?q=*&sort=display-name-asc"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for store in response.json()["results"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("Hemköp ")
            item["phone"] = store["address"]["phoneNumber"]
            item["website"] = "https://www.hemkop.se/butik/{}".format(item["ref"])

            try:
                item["opening_hours"] = OpeningHours()
                for rule in store["openingHours"]:
                    day, times = rule.split(" ")
                    start_time, end_time = times.split("-")
                    if day := sanitise_day(day, DAYS_SE):
                        item["opening_hours"].add_range(day, start_time, end_time)
            except:
                pass

            yield item
