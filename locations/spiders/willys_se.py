import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_SE, OpeningHours, sanitise_day


class WillysSESpider(scrapy.Spider):
    name = "willys_se"
    item_attributes = {"brand": "Willys", "brand_wikidata": "Q10720214"}
    start_urls = ["https://www.willys.se/axfood/rest/search/store?q=*&sort=display-name-asc"]

    def parse(self, response):
        for store in response.json()["results"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("Wh ").removeprefix("Willys ")
            item["phone"] = store["address"]["phoneNumber"]
            item["website"] = "https://www.willys.se/butik/{}".format(item["ref"])

            item["opening_hours"] = OpeningHours()
            for rule in store["openingHours"]:
                if "stängd" not in rule:
                    day, times = rule.split(" ")
                    start_time, end_time = times.split("-")
                    if day := sanitise_day(day, DAYS_SE):
                        item["opening_hours"].add_range(day, start_time, end_time)

            yield item
