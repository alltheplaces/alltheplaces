from datetime import datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class BallaratCityCouncilTreesAUSpider(OpendatasoftExploreSpider):
    name = "ballarat_city_council_trees_au"
    item_attributes = {"operator": "Ballarat City Council", "operator_wikidata": "Q132478165", "state": "VIC", "nsi_id": "N/A"}
    api_endpoint = "https://data.ballarat.vic.gov.au/api/explore/v2.1/"
    dataset_id = "trees"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["ref"])
        apply_category(Categories.NATURAL_TREE, item)
        if species := feature.get("species"):
            if species != "Not Assessed" and species != "Not Recorded":
                item["extras"]["species"] = species
        item["extras"]["protected"] = "yes"
        if dbh_range_cm := feature.get("dbh"):
            if dbh_range_cm != "Not Assessed" and dbh_range_cm != "Not Recorded":
                dbh_range_cm = dbh_range_cm.replace("<", "0-").replace(" cm - ", "-").replace("cm - ", "-").replace("cm", " cm")
                item["extras"]["diameter:range"] = f"{dbh_range_cm}"
        if diameter_crown_range_m := feature.get("crown"):
            if diameter_crown_range_m != "Not Assessed" and diameter_crown_range_m != "Not Recorded":
                diameter_crown_range_m = diameter_crown_range_m.replace("<", "0-").replace("m", " m")
                item["extras"]["diameter_crown:range"] = f"{diameter_crown_range_m}"
        if height_range_m := feature.get("height"):
            if height_range_m != "Not Assessed" and height_range_m != "Not Recorded":
                height_range_m = height_range_m.replace("<", "0-")
                item["extras"]["height:range"] = f"{height_range_m} m"
        if planted_date_str := feature.get("planted"):
            try:
                planted_date = datetime.fromisoformat(planted_date_str)
                item["extras"]["start_date"] = planted_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
        yield item
