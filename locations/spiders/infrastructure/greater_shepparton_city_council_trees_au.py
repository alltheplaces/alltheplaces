from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GreaterSheppartonCityCouncilTreesAUSpider(JSONBlobSpider):
    name = "greater_shepparton_city_council_trees_au"
    item_attributes = {"operator": "Greater Shepparton City Council", "operator_wikidata": "Q133830205", "state": "VIC"}
    allowed_domains = ["data.gov.au"]
    start_urls = [
        "https://data.gov.au/data/dataset/e794491f-2eb7-4035-8b0c-f7248c28feda/resource/8f46fcc0-778c-44d3-bba6-38ac9120123e/download/greater_shepparton_city_council_street_and_park_trees.json"
    ]
    locations_key = ["features"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["genus"] = feature["genus"]
        item["extras"]["species"] = feature["species"]

        dbh_min_cm = feature.get("dbh_min")
        dbh_max_cm = feature.get("dbh_max")
        if dbh_min_cm and dbh_max_cm:
            item["extras"]["diameter:range"] = f"{dbh_min_cm} - {dbh_max_cm} cm"
        elif dbh_cm := feature.get("dbh"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"

        dcrown_min_m = feature.get("crown_min")
        dcrown_max_m = feature.get("crown_max")
        if dcrown_min_m and dcrown_max_m:
            item["extras"]["diameter_crown:range"] = f"{dcrown_min_m} - {dcrown_max_m} m"
        elif dcrown_m := feature.get("crown"):
            item["extras"]["diameter_crown"] = f"{dcrown_m} m"

        height_min_m = feature.get("height_min")
        height_max_m = feature.get("height_max")
        if height_min_m and height_max_m:
            item["extras"]["height:range"] = f"{height_min_m} - {height_max_m} m"
        elif height_m := feature.get("height"):
            item["extras"]["diameter"] = f"{height_m} m"

        yield item
