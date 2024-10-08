import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class IngSpider(scrapy.Spider):
    name = "ing"
    item_attributes = {"brand": "ING", "brand_wikidata": "Q645708"}
    start_urls = [
        "https://api.www.ing.nl/locator/offices",
        "https://api.www.ing.be/locator/offices",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for store in response.json().get("locations"):
            if store["type"] == "ISP":
                # Not clear what these "service points" are, skipping for now
                continue
            address_details = store.get("address")
            yield JsonRequest(
                f"https://api.www.ing.nl/locator/offices/{store.get('id')}",
                callback=self.parse_store,
                meta={
                    "housenumber": address_details.get("number"),
                    "street": address_details.get("street"),
                    "postcode": address_details.get("postalCode"),
                    "city": address_details.get("city"),
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "name": store.get("name"),
                },
            )

    def parse_store(self, response):
        store = response.json()
        oh = OpeningHours()
        for hours in store.get("timetable").get("office"):
            for day_hours in hours.get("hours", []):
                if day := sanitise_day(hours["day"]):
                    oh.add_range(day, day_hours["open"], day_hours["closed"])

        item = Feature(
            {
                "ref": store.get("id"),
                "street": response.meta.get("street"),
                "housenumber": response.meta.get("housenumber"),
                "postcode": response.meta.get("postcode"),
                "city": response.meta.get("city"),
                "country": store.get("country"),
                "email": store.get("email"),
                "phone": store.get("phone"),
                "lat": response.meta.get("lat"),
                "lon": response.meta.get("lon"),
                "opening_hours": oh,
            }
        )

        if code := store.get("code"):
            if code == "001":
                item["branch"] = response.meta["name"].removeprefix("ING ")
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)
        elif store["type"] == "ING-kantoor":
            apply_category(Categories.BANK, item)
            item["branch"] = response.meta["name"]

        yield item
