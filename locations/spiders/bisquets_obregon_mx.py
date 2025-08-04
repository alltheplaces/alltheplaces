from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BisquetsObregonMXSpider(JSONBlobSpider):
    name = "bisquets_obregon_mx"
    item_attributes = {"brand": "Bisquets Obregón", "brand_wikidata": "Q131450266"}
    allowed_domains = ["api-stg.bisapp.net"]
    start_urls = [
        "https://api-stg.bisapp.net/api/sucursales-page?populate[general_banners][populate]=*&populate[sucursal_items][populate]=*&populate[sucursal_items][filters][branch_type]=restaurante"
    ]
    locations_key = ["data", "sucursal_items"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["addr_full"] = feature["branch_address"]
        item["state"] = feature["branch_region"]
        item["lat"] = feature["branch_latitude"]
        item["lon"] = feature["branch_longitude"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(
            DAYS, feature["opening_time"].split(".", 1)[0], feature["closing_time"].split(".", 1)[0], "%H:%M:%S"
        )
        apply_category(Categories.RESTAURANT, item)
        if description := feature.get("branch_description"):
            apply_yes_no(Extras.WIFI, item, "WIFI gratis" in description)
        yield item
