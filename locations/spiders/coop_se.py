import scrapy

from locations.hours import DAYS_SE, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class CoopSESpider(scrapy.Spider):
    name = "coop_se"
    item_attributes = {"brand": "Coop", "brand_wikidata": "Q15229319", "country": "SE"}
    start_urls = ["https://proxy.api.coop.se/external/store/stores?api-version=v2"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"ocp-apim-subscription-key": "990520e65cc44eef89e9e9045b57f4e9"}}

    def parse(self, response, **kwargs):
        for store in response.json().get("stores"):
            yield scrapy.Request(
                f"https://proxy.api.coop.se/external/store/stores/{store.get('ledgerAccountNumber')}?api-version=v3",
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store = response.json()
        oh = OpeningHours()
        for opening_hour in store.get("openingHours"):
            if "-" in opening_hour["text"]:
                start_day, end_day = opening_hour["text"].split("-", maxsplit=1)
            else:
                start_day = end_day = opening_hour["text"]
            start_day = sanitise_day(start_day, DAYS_SE)
            end_day = sanitise_day(end_day, DAYS_SE)
            if start_day and end_day:
                for day in day_range(start_day, end_day):
                    oh.add_range(day, opening_hour["openFrom"], opening_hour["openTo"], time_format="%H:%M:%S")

        yield Feature(
            {
                "ref": str(store.get("id")),
                "name": store.get("name"),
                "street_address": store.get("address"),
                "postcode": store.get("postalCode"),
                "city": store.get("city"),
                "phone": store.get("phone"),
                "website": f"https://www.coop.se{store.get('url')}" if store.get("url") else None,
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "opening_hours": oh,
                "extras": {"store_type": store.get("concept").get("name")},
            }
        )
