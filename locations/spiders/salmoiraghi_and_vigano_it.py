from typing import Iterable

import scrapy
from scrapy.http import JsonRequest, Request, Response

from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SalmoiraghiAndViganoITSpider(JSONBlobSpider):
    name = "salmoiraghi_and_vigano_it"
    item_attributes = {"brand": "Salmoiraghi & Viganò", "brand_wikidata": "Q21272314"}
    locations_key = "records"

    def start_requests(self) -> Iterable[JsonRequest | Request]:
        for lat, lng in point_locations("eu_centroids_120km_radius_country.csv", "IT"):
            yield scrapy.Request(
                url=f"https://api-tab.luxottica.com/tl-store-locator/api/v1/SV/offices?latitude={lat}&longitude={lng}&radius=100&limit=1000&offset=0&officeTypes=BOUTIQUE"
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = feature["address"].get("address")
        item["ref"] = feature["storeNumber"]
        item["opening_hours"] = OpeningHours()
        for day in feature["officeHours"]:
            if not day["isClosed"]:
                item["opening_hours"].add_range(day["dayOfWeek"], day["opening"], day["closing"])
        yield item
