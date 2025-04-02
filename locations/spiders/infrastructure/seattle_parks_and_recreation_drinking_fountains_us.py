from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationDrinkingFountainsUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_drinking_fountains_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Drinking_Fountain"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("CURRENT_STATUS") == "OFF":
            return
        item["ref"] = feature["AMWOID"]
        if name := feature.get("EQUIPDESC"):
            item["name"] = name.replace(" DRINK FOUNT", " DRINKING FOUNTAIN")
        apply_category(Categories.BUBBLER, item)
        if feature.get("DOG_BOWL") == "Yes":
            apply_category(Categories.DOG_BOWL_FOUNTAIN, item)
        if feature.get("BOTTLE_FILLTER") == "Yes":
            apply_category(Categories.BOTTLE_REFILL_FOUNTAIN, item)
        yield item
