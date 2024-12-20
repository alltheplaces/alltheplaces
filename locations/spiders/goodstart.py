import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, day_range


class GoodstartSpider(scrapy.Spider):
    name = "goodstart"
    item_attributes = {
        "brand": "GoodStart Early Learning",
        "brand_wikidata": "Q24185325",
    }
    allowed_domains = ["goodstart.org.au"]
    start_urls = [
        "https://www.goodstart.org.au/find-centre/api/get-centres/-35.0004451/138.3309724/10000/",
    ]

    def parse(self, response):
        for i in response.json()["centres"]:
            item = DictParser.parse(i)
            item["website"] = "https://www.goodstart.org.au" + item.pop("website")
            item["image"] = "https://www.goodstart.org.au" + i["imageUrl"]
            item["addr_full"] = i["fullAddress"]
            item["street_address"] = i["address"]
            item["city"] = i["suburb"]
            item["opening_hours"] = OpeningHours()
            if "," in i["hours"]:
                (hour_range, days_range) = i["hours"].replace("–", "to").split(", ")
                (from_time, close_time) = hour_range.replace(".", ":").split(" to ")
                (start_day, end_day) = days_range.split(" to ")
                for day in day_range(DAYS_EN[start_day], DAYS_EN[end_day.replace(".", "")]):
                    item["opening_hours"].add_range(day, from_time, close_time, time_format="%I:%M%p")
            apply_category(Categories.CHILD_CARE, item)
            yield item
