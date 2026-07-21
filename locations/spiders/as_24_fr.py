from typing import Iterable

from scrapy.http import Response

from locations.categories import Access, Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

FUEL_MAPPING = {
    "01": Fuel.DIESEL,
    "03": Fuel.BIODIESEL,
    "10": Fuel.ADBLUE,
    "95": Fuel.BIODIESEL,
    "BIOGNC": Fuel.CNG,
    "GL": Fuel.LNG,
}


class As24FRSpider(JSONBlobSpider):
    name = "as_24_fr"
    item_attributes = {"brand": "AS 24", "brand_wikidata": "Q2819394"}
    start_urls = ["https://network.as24.com/stationfinderservices/services/stations"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        filtered_json = []
        for poi in response.json():
            if poi["countryCode"] == "FRA" and poi["products"] and "08" not in poi["products"] and poi["status"] == 1:
                filtered_json.append(poi)
        return filtered_json

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["stationId"]
        item["street_address"] = item.pop("addr_full")
        item["website"] = f"https://network.as24.com/stationfinder/en/stations/{item['ref']}"
        self.parse_fuel(item, feature)
        apply_yes_no(Access.HGV, item, True)
        apply_category(Categories.FUEL_STATION, item)
        yield item

    def parse_fuel(self, item, poi):
        for fuel in poi["products"]:
            if tag := FUEL_MAPPING.get(fuel):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/as_24_fr/fuel/unknown/{fuel}")
