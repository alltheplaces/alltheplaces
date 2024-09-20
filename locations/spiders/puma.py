import re

import pycountry
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider

PUMA_BRANDS = {
    "PUMA FASHION": {"brand": "Puma", "brand_wikidata": "Q157064"},
    "PUMA KIDS": {"brand": "Puma Kids", "brand_wikidata": "Q157064"},
    "PUMA STORE": {"brand": "Puma", "brand_wikidata": "Q157064"},
    "PUMA OUTLET": {"brand": "Puma Outlet", "brand_wikidata": "Q157064"},
}


class PumaSpider(JSONBlobSpider):
    name = "puma"
    countries = [cc.alpha_2 for cc in pycountry.countries]
    countries_to_skip = ["TW"]  # existing spider
    for country in countries_to_skip:
        countries.pop(countries.index(country))
    start_urls = [f"https://prod.storelocator.puma.com/api/stores?market={cc}" for cc in countries]

    def start_requests(self):
        self.brand_name_regex = re.compile(r"^(" + "|".join(PUMA_BRANDS) + r") ", re.IGNORECASE)
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse)

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_CLOTHES, item)
        if m := self.brand_name_regex.match(item["name"]):
            item.update(PUMA_BRANDS[m.group(1).upper()])
            item["branch"] = item["name"].replace(self.brand_name_regex.match(item["name"]).group(1), "").strip()
            item["name"] = item["brand"]
        else:
            item.update(PUMA_BRANDS["PUMA STORE"])
            # Not moving name to branch because of locations in scripts I don't know. Leave given name as name for now
        item["street_address"] = item.pop("street")
        # Can't tell what the channel does, but it is required.
        # May be different by default for different countries, and only seems to change the image info very slightly
        yield JsonRequest(
            url=f"https://prod.storelocator.puma.com/api/stores/{location['id']}?channel=677",
            callback=self.parse_opening_hours,
            meta={"item": item},
        )

    def parse_opening_hours(self, response):
        item = response.meta["item"]
        location = response.json()

        item["phone"] = location.get("phone")
        item["email"] = location.get("email")

        item["opening_hours"] = OpeningHours()
        days_added = []
        for day_hours in location["openingHours"]:
            day = DAYS[(day_hours["open"]["day"] - 1) % 7]
            days_added.append(day)
            item["opening_hours"].add_range(day, day_hours["open"]["time"], day_hours["close"]["time"], "%H%M")
        # Website displays missing days as closed
        for day in DAYS:
            if day not in days_added:
                item["opening_hours"].set_closed(day)

        yield item
