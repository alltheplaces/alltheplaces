import scrapy

from locations.hours import DAYS_SE, OpeningHours
from locations.items import Feature


class CoopNOSpider(scrapy.Spider):
    name = "coop_se"
    item_attributes = {"brand": "Coop", "brand_wikidata": "Q15229319", "country": "SE"}
    start_urls = ["https://proxy.api.coop.se/external/store/stores/?api-version=v1"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "ocp-apim-subscription-key": "990520e65cc44eef89e9e9045b57f4e9",
        },
    }

    def parse(self, response, **kwargs):
        for store in response.json().get("stores"):
            yield scrapy.Request(
                f"https://proxy.api.coop.se/external/store/stores/{store.get('ledgerAccountNumber')}?api-version=v1",
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store = response.json()
        oh = OpeningHours()
        for opening_hour in store.get("openingHours"):
            day = opening_hour.get("text")
            if "-" not in day:
                oh.add_range(DAYS_SE.get(day), opening_hour.get("openFrom")[:5], opening_hour.get("openTo")[:5])
            else:
                split_day = day.split("-")
                found_first_day = False
                for se_day in DAYS_SE:
                    if found_first_day or se_day in split_day:
                        oh.add_range(
                            DAYS_SE.get(se_day), opening_hour.get("openFrom")[:5], opening_hour.get("openTo")[:5]
                        )
                        found_first_day = True
                        if split_day[1] == se_day:
                            break

        yield Feature(
            {
                "ref": store.get("id"),
                "name": store.get("name"),
                "street_address": store.get("address"),
                "phone": store.get("phone"),
                "website": f"https://www.coop.se{store.get('url')}" if store.get("url") else None,
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "opening_hours": oh.as_opening_hours(),
                "extras": {"store_type": store.get("concept").get("name")},
            }
        )
