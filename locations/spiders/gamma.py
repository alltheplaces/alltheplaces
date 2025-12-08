import scrapy

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class GammaSpider(scrapy.Spider):
    name = "gamma"
    item_attributes = {"brand": "Gamma", "brand_wikidata": "Q2294120"}
    start_urls = [
        "https://api.gamma.nl/store/2/stores",
        "https://api.gamma.be/store/2/stores",
    ]

    def parse(self, response):
        for store in response.json():
            if "webshop" in store["slug"]:
                continue

            address_details = store.get("address")
            coordinates = store.get("geoLocation")
            country_code = address_details.get("country")
            base_website = f"https://www.gamma.{country_code.lower()}"
            formatted_website = (
                f"{base_website}/fr/magasins-et-heures-ouverture/{store.get('slug')}"
                if country_code == "BE"
                else f"{base_website}/bouwmarkten/{store.get('slug')}"
            )
            oh = OpeningHours()
            for day, hours in store.get("openingSchedule").get("regular").items():
                oh.add_range(
                    day=sanitise_day(day),
                    open_time=hours.get("opens"),
                    close_time=hours.get("closes"),
                    time_format="%H:%M:%S",
                )
            yield Feature(
                {
                    "ref": store.get("uid"),
                    "name": store.get("name"),
                    "housenumber": address_details.get("streetNumber"),
                    "street": address_details.get("street"),
                    "country": address_details.get("country"),
                    "phone": address_details.get("phoneNumber"),
                    "postcode": address_details.get("postalCode"),
                    "city": address_details.get("city"),
                    "lat": coordinates.get("latitude"),
                    "lon": coordinates.get("longitude"),
                    "website": formatted_website,
                    "opening_hours": oh,
                }
            )
