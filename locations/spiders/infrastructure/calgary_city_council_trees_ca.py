from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class CalgaryCityCouncilTreesCASpider(SocrataSpider):
    name = "calgary_city_council_trees_ca"
    item_attributes = {"operator": "Calgary City Council", "operator_wikidata": "Q4145705", "state": "AB"}
    host = "data.calgary.ca"
    resource_id = "tfs4-3wwa"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["asset_type"] == "STUMP":
            return
        item["ref"] = feature["wam_id"]
        if street_address := feature.get("location_detail"):
            item["street_address"] = street_address
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["genus"] = feature["genus"]
        item["extras"]["species"] = feature["species"]
        item["extras"]["taxon:en"] = feature["common_name"]
        if dbh_cm := feature.get("dbh_cm"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        yield item
