import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class NewyorkerSpider(scrapy.Spider):
    name = "newyorker"
    start_urls = ["https://api.newyorker.de/csp/stores/store/query?limit=10000"]

    item_attributes = {"brand": "New Yorker", "brand_wikidata": "Q706421"}

    def parse(self, response, **kwargs):
        for store in response.json().get("items"):
            oh = OpeningHours()
            for day in store["opening_times"]:
                oh.add_range(
                    day=sanitise_day(day.get("week_day")), open_time=day.get("opening"), close_time=day.get("closing")
                )
            address_data = store["address"]
            item = DictParser.parse(store)
            item["name"] = address_data["headline"]
            item["addr_full"] = ", ".join(
                filter(
                    None,
                    [address_data["address_line_1"], address_data["address_line_2"], address_data["address_line_3"]],
                )
            )
            item["phone"] = address_data["phone"]
            item["opening_hours"] = oh
            yield item
