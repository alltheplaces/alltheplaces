import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LiquorCityZASpider(scrapy.Spider):
    name = "liquor_city_za"
    item_attributes = {"brand": "Liquor City", "brand_wikidata": "Q116620538"}
    start_urls = [
        "https://lets-trade-client-prod.letstrade.global/v2/client/branches?client_id=689053976a0872f147baef68"
    ]

    def parse(self, response):
        for location in response.json()["content"]["branch_list"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["ref"] = location["_id"]
            oh = OpeningHours()
            for day_time in location["working_hours"]:
                day = day_time["day"]
                if day != "Public Holidays":
                    open_time = day_time["from"]
                    close_time = day_time["to"]
                    oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
            yield item
