from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class EdmontonCityCouncilTreesCASpider(SocrataSpider):
    name = "edmonton_city_council_trees_ca"
    item_attributes = {"operator": "Edmonton City Council", "operator_wikidata": "Q4145705", "state": "AB"}
    host = "data.edmonton.ca"
    resource_id = "eecg-fc54"
    no_refs = True  # Reference IDs only available for some (not all) trees.

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["genus"] = feature["genus"]
        item["extras"]["species"] = feature["species_botanical"]
        item["extras"]["taxon:en"] = feature["species"]
        if dbh_cm := feature.get("diameter_breast_height"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        if planted_date := feature.get("planted_date"):
            planted_date = planted_date.replace("/", "-").split("T", 1)[0]
            if planted_date != "1990-01-01":
                item["extras"]["start_date"] = planted_date
        yield item
