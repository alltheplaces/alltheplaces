import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class PizzaHutCLSpider(scrapy.Spider):
    name = "pizza_hut_cl"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615", "extras": Categories.RESTAURANT.value}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.mer-cat.com/v1/stores/all",
            headers={"PROJECT_ID": "WEB", "Accept": "application/json", "X-PLATFORM": "web", "X-TENANT": "pizzahut"},
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = store.get("text_address")
            item["website"] = "https://pizzahut.cl/tiendas/"
            oh = OpeningHours()
            for hours in store.get("business_hours"):
                day = hours["day"].capitalize()
                if day in DAYS_EN:
                    oh.add_range(
                        day,
                        hours["opening_time"].split(" ")[1],
                        hours["closing_time"].split(" ")[1],
                        time_format="%H:%M:%S",
                    )
            item["opening_hours"] = oh
            yield item
