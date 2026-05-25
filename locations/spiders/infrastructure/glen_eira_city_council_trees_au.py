import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GlenEiraCityCouncilTreesAUSpider(JSONBlobSpider):
    name = "glen_eira_city_council_trees_au"
    item_attributes = {"operator": "Glen Eira City Council", "operator_wikidata": "Q56477767", "state": "VIC"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = [
        "https://connect.pozi.com/userdata/gleneira-publisher/Council-Facilities-and-Services/Park_and_Street_Trees.json"
    ]
    locations_key = "features"
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_WARNSIZE": 67108864}  # Avoid HTTP 403 error  # Data is >32MiB

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "Alive" not in feature["Tree_Status"]:
            return
        item["ref"] = feature["feature_id"]
        if addr := feature.get("feature_location"):
            if located_in := re.match(r"^([^\(]+)\(([^\)]+)\)$", addr):
                item["addr_full"] = located_in.group(1)
                item["located_in"] = located_in.group(2)
            else:
                item["addr_full"] = addr
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["alt_ref"] = feature["central_asset_id"]
        if species := feature.get("Botanical"):
            item["extras"]["species"] = species
        if common_name := feature.get("Common_Name"):
            item["extras"]["taxon:en"] = common_name
        if dbh_cm := feature.get("DBH"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        if crown_diameter_m := feature.get("Spread"):
            item["extras"]["diameter_crown"] = f"{crown_diameter_m} m"
        if height_m := feature.get("Height"):
            item["extras"]["height"] = f"{height_m}"
        yield item
