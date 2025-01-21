import urllib

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class OfficeworksAUSpider(scrapy.Spider):
    name = "officeworks_au"
    item_attributes = {"brand": "Officeworks", "brand_wikidata": "Q7079486"}
    allowed_domains = ["www.officeworks.com.au"]
    start_urls = [
        "https://www.officeworks.com.au/catalogue-app/api/stores/?coordinates=-23.07,132.08&activeOnly=true&limit=10000"
    ]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["website"] = (
                "https://www.officeworks.com.au/shop/officeworks/storepage/"
                + item["ref"].strip()
                + "/"
                + item["state"].strip()
                + "/"
                + item["city"].strip()
            )
            item["website"] = urllib.parse.quote(item["website"], safe=":/?=&")
            oh = OpeningHours()
            for day in store["openingHours"]:
                oh.add_range(day["dayOfWeek"], day["open"], day["close"], "%I%p")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
