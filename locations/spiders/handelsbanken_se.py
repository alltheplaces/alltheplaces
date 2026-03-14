import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class HandelsbankenSESpider(Spider):
    name = "handelsbanken_se"
    item_attributes = {"brand": "Handelsbanken", "brand_wikidata": "Q1421630"}
    start_urls = ["https://locator.maptoweb.dk/handelsbanken.com/locator/points/where/CountryCode/eqi/se"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["results"]:
            oh = OpeningHours()
            location_type = None
            for options in store.get("options"):
                if options.get("name") == "LocationType":
                    location_type = options.get("value")
                if options.get("name") != "OpenHoursSpan":
                    continue
                oh_json = json.loads(options.get("value"))
                for day in oh_json:
                    oh.add_range(DAYS[int(day.get("Weekday"))], day.get("Open"), day.get("Close"))
            website = store.get("url")
            if website and website.startswith("www."):
                website = "https://" + website
            properties = {
                "ref": str(store.get("id")),
                "housenumber": store.get("houseNumber"),
                "postcode": store.get("zipCode"),
                "city": store.get("cityName"),
                "country": store.get("countryCode"),
                "street_address": store.get("streetName"),
                "phone": store.get("phone"),
                "email": store.get("email"),
                "website": website,
                "lat": store.get("location").get("lat"),
                "lon": store.get("location").get("lng"),
                "opening_hours": oh,
            }
            if location_type in ["ATM", "CRS"]:
                apply_category(Categories.ATM, properties)
                apply_yes_no("cash_out", properties, location_type == "CRS")
            elif location_type == "Branch":
                properties["branch"] = store.get("name")
                apply_category(Categories.BANK, properties)
            yield Feature(**properties)
