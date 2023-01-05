import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import GeojsonPointItem


class OttosCHSpider(scrapy.Spider):
    name = "ottos_ch"
    item_attributes = {"brand": "Otto’s", "brand_wikidata": "Q2041507"}
    allowed_domains = ["www.ottos.ch"]
    start_urls = ("https://www.ottos.ch/de/ottos-filialen",)

    def parse(self, response):
        opening_hours = {}
        for store in response.xpath("//span[@data-amid]"):
            key = store.css(".location_header").xpath("text()").get()
            opening_hours[key] = self.parse_opening_hours(store)

        js = re.search("jsonLocations:(.*),", response.text).group(1)
        for store in json.loads(js)["items"]:
            props = {
                "lat": float(store["lat"]),
                "lon": float(store["lng"]),
                "name": "Otto’s",
                "city": store["city"],
                "country": store["country"],
                "opening_hours": opening_hours.get(store["name"]),
                "phone": store["phone"],
                "postcode": store["zip"],
                "ref": store["id"],
                "street_address": store["address"],
            }
            item = GeojsonPointItem(**props)
            apply_category(Categories.SHOP_VARIETY_STORE, item)
            yield item

    @staticmethod
    def parse_opening_hours(store):
        oh = OpeningHours()
        s = store.xpath('div[@class="all_schedule"]//text()').getall()
        for i, text in enumerate([t.strip() for t in s]):
            tokens = text.split()
            if len(tokens) != 2 or tokens[0] not in DAYS_DE:
                continue
            day = DAYS_DE[tokens[0]]
            h = s[i + 1].split()
            if len(h) != 3 or h[1] != "-":
                continue
            oh.add_range(day, h[0], h[2])
        return oh.as_opening_hours()
