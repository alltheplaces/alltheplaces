from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationSwimmingBeachesUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_swimming_beaches_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Swimming_Beaches"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        if phone := item.get("phone"):
            if len(phone) == 8 and phone[3] == "-":
                item["phone"] = f"206-{phone}"
        apply_category(Categories.NATURAL_BEACH, item)
        yield item
