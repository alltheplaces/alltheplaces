from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationTennisCourtsUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_tennis_courts_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Tennis_Courts"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["AMWO_ID"]
        if courts := feature.get("NUMCOURTS"):
            if courts > 1:
                apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            else:
                apply_category(Categories.LEISURE_PITCH, item)
        apply_category({"sport": "tennis"}, item)
        if lit := feature.get("LIGHTS"):
            if lit == "Yes":
                item["extras"]["lit"] = "yes"
            elif lit == "No":
                item["extras"]["lit"] = "no"
        yield item
