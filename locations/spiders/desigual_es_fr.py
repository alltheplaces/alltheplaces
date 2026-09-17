import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours


class DesigualESFRSpider(scrapy.Spider):
    name = "desigual_es_fr"
    item_attributes = {"brand": "Desigual", "brand_wikidata": "Q83750", "name": "Desigual"}
    start_urls = [
        "https://www.desigual.com/fr_FR/magasins/",
        "https://www.desigual.com/es_ES/tiendas/",
    ]

    def parse(self, response, **kwargs):
        for city_url in response.xpath("//a[@data-city-name]/@href").getall():
            yield scrapy.Request(city_url, callback=self.parse_city)

    def parse_city(self, response, **kwargs):
        # Store data for every store in the city is embedded as JSON on a Vue
        # component attribute, so no need to visit each store's own page.
        stores_json = response.xpath('//maps-wrapper/@*[name()=":initial-stores"]').get()
        if not stores_json or stores_json == "null":
            return

        for store in json.loads(stores_json).get("stores", []):
            if "AUTHORIZED DEALER" in store.get("name", "").upper():
                # Third-party multi-brand retailers, not Desigual's own stores.
                continue

            item = DictParser.parse(store)
            item["website"] = store.get("detailUrl")
            item["branch"] = item.pop("name", "").removeprefix("Desigual ")

            if store.get("id") == "R771":
                # Desigual's own data has lat/lon transposed for this one store.
                item["lat"], item["lon"] = item["lon"], item["lat"]

            item["opening_hours"] = OpeningHours()
            for day in store.get("schedule", []):
                if day.get("isOpen") and day.get("open") and day.get("close"):
                    item["opening_hours"].add_range(DAYS_FROM_SUNDAY[day["dayNumber"] - 1], day["open"], day["close"])

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
