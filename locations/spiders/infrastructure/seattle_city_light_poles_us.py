from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleCityLightPolesUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_city_light_poles_us"
    item_attributes = {"operator": "Seattle City Light", "operator_wikidata": "Q7442080", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "SCL_Poles"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["ASSET_ID"])
        apply_category(Categories.POWER_POLE, item)
        if feature.get("IS_STREETLIGHT") == "Yes":
            apply_category(Categories.STREET_LAMP, item)
        if height_ft := feature.get("HEIGHT"):
            item["extras"]["height"] = f"{height_ft}'"
        yield item
