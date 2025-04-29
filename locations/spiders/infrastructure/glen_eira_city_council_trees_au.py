from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GlenEiraCityCouncilTreesAUSpider(JSONBlobSpider):
    name = "glen_eira_city_council_trees_au"
    item_attributes = {"operator": "Glen Eira City Council", "operator_wikidata": "Q56477767", "state": "VIC"}
    allowed_domains = ["data.gov.au"]
    start_urls = [
        "https://data.gov.au/data/dataset/ed15e3ea-48dc-47d2-afa6-518e6f5276e1/resource/85c2d44c-8ccf-4a32-9881-872f1a511ef7/download/streetandparktrees.json"
    ]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["feature_id"]
        apply_category(Categories.NATURAL_TREE, item)
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
