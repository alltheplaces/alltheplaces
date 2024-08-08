from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PurebabyAUSpider(Spider):
    name = "purebaby_au"
    item_attributes = {"brand": "Purebaby", "brand_wikidata": "Q122431533"}
    allowed_domains = ["purebaby.com.au"]
    start_urls = ["https://purebaby.com.au/page-data/pages/stores/page-data.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["result"]["data"]["stores"]["edges"]:
            if "purebaby-" not in location["node"]["handle"]["current"]:
                continue
            item = DictParser.parse(location["node"])
            item["website"] = "https://purebaby.com.au/pages/stores/" + location["node"]["url"]
            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_hours in location["node"]["openhours"]:
                day_name = day_hours["day"]
                hours_range = day_hours["hours"]
                hours_string = f"{hours_string} {day_name}: {hours_range}"
            item["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
