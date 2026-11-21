import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

FUELS = {
    "A-95": Fuel.OCTANE_95,
    "upg95": Fuel.OCTANE_95,
    "upg100": Fuel.OCTANE_100,
    "EURO DIESEL": Fuel.DIESEL,
    "upgDIESEL": Fuel.DIESEL,
    "Газ": Fuel.LPG,
    "AdBlue": Fuel.ADBLUE,
}
SERVICES = {
    "WC": Extras.TOILETS,
    "Wi-Fi": Extras.WIFI,
    "Підкачка шин": Extras.COMPRESSED_AIR,
    "Дизель генератор": Extras.BACKUP_GENERATOR,
}


class UpgUASpider(JSONBlobSpider):
    name = "upg_ua"
    item_attributes = {"brand": "UPG", "brand_wikidata": "Q117706281"}
    start_urls = ["https://upg.ua/merezha_azk/"]

    def extract_json(self, response: TextResponse) -> list:
        script = response.xpath('//script[contains(text(), "var objmap")]/text()').get()
        return json.JSONDecoder().raw_decode(script[script.index("{") :])[0]["data"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # The name ends with the station hours, or with the cafe hours after a 🍽
        if "цілодобово" in feature["FullName"]:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        elif "🍽" not in feature["FullName"] and "(" in feature["FullName"]:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, *feature["FullName"].split("(")[1].strip(")").split(" – "))
        for fuel in feature["FuelsAsArray"]:
            apply_yes_no(FUELS[fuel["Title"]], item, True)
        services = {service["Title"] for service in feature["ServicesAsArray"]}
        for title, extra in SERVICES.items():
            apply_yes_no(extra, item, title in services)
        apply_category(Categories.FUEL_STATION, item)
        yield item
