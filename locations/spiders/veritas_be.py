import json

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class VeritasBESpider(scrapy.Spider):
    name = "veritas_be"
    start_urls = ["https://www.veritas.be/fr_be/stores"]
    item_attributes = {"brand": "Veritas", "brand_wikidata": "Q56239194"}

    def parse(self, response, **kwargs):
        stores_json = json.loads(
            response.xpath(
                '//script[contains(text(), "store-locator-search") and @type="text/x-magento-init"]/text()'
            ).get()
        )

        for store in (
            stores_json.get("*")
            .get("Magento_Ui/js/core/app")
            .get("components")
            .get("store-locator-search")
            .get("markers")
        ):
            opening_hours = OpeningHours()
            website = store.get("url_key")
            ohs = store.get("schedule").get("openingHours")
            for day_index, hours in enumerate(ohs):
                for hour in hours:
                    opening_hours.add_range(DAYS[day_index], hour.get("start_time"), hour.get("end_time"))
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "addr_full": store.get("address"),
                    "street_address": store.get("street")[0],
                    "phone": store.get("contact_phone"),
                    "postcode": store.get("postCode"),
                    "city": store.get("city"),
                    "website": f"https://www.veritas.be/fr_be/stores/{website}" if website else None,
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "opening_hours": opening_hours,
                }
            )
