from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ThirstyCamelAUSpider(Spider):
    name = "thirsty_camel_au"
    item_attributes = {
        "brand": "Thirsty Camel",
        "brand_wikidata": "Q113503937",
        "extras": Categories.SHOP_ALCOHOL.value,
    }
    allowed_domains = ["api.beta.thirstycamel.com.au"]
    start_urls = ["https://api.beta.thirstycamel.com.au/stores/all"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if not location.get("published") or location.get("deletedAt"):
                continue
            item = DictParser.parse(location)
            item["geometry"] = location["point"]
            item["website"] = "https://www.thirstycamel.com.au/stores/" + location["slug"]
            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_name, day_hours in location["hours"].items():
                if not day_hours:
                    continue
                open_time = day_hours[0]
                close_time = day_hours[1]
                hours_string = f"{hours_string} {day_name}: {open_time} - {close_time}"
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
