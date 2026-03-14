from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class EpcorFireHydrantsCASpider(SocrataSpider):
    name = "epcor_fire_hydrants_ca"
    item_attributes = {"operator": "EPCOR", "operator_wikidata": "Q5323849", "state": "AB"}
    host = "data.edmonton.ca"
    resource_id = "x4n2-2ke2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["hydrant_number"]
        item["street_address"] = feature.get("nearest_address")
        apply_category(Categories.FIRE_HYDRANT, item)
        if installation_year := feature.get("installation_year"):
            item["extras"]["start_date"] = installation_year
        if flow_rate := feature.get("flow_rate"):
            item["extras"]["flow_rate"] = flow_rate.removeprefix(">").strip()
        yield item
