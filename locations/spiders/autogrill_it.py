import scrapy

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AutogrillITSpider(scrapy.Spider):
    name = "autogrill_it"
    item_attributes = {"brand": "Autogrill", "brand_wikidata": "Q786790"}
    start_urls = [
        "https://api.onthemap.io/server/v1/api/location?dataset=puntivendita%2Cbrandterzi&key=05eaef09-4435-11eb-8d51-cb3137bac506"
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["data"]["results"]["features"]:
            store.update(store.pop("properties"))
            item = Feature()
            item["geometry"] = store.get("geometry")
            item["branch"] = store.get("Nome attività").replace("Autogrill ", "").lstrip()
            item["street_address"] = merge_address_lines(
                [
                    store.get("Riga indirizzo 1"),
                    store.get("Riga indirizzo 2"),
                    store.get("Riga indirizzo 3"),
                    store.get("Riga indirizzo 4"),
                    store.get("Riga indirizzo 5"),
                ]
            )
            item["postcode"] = store.get("Codice postale")
            item["city"] = store.get("Località")
            item["phone"] = store.get("Telefono principale")
            item["state"] = store.get("Area amministrativa")
            item["ref"] = store.get("otm_id")

            apply_yes_no(Extras.WIFI, item, store.get("Wi-fi") == "TRUE")
            yield item
