from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BarwonWaterRecycledFireHydrantsAUSpider(ArcGISFeatureServerSpider):
    name = "barwon_water_recycled_fire_hydrants_au"
    item_attributes = {"operator": "Barwon Water", "operator_wikidata": "Q4865988"}
    host = "services8.arcgis.com"
    context_path = "uLK1YQYKdEhgFHsx/ArcGIS"
    service_id = "Barwon_Water_Fire_Services"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        apply_category(Categories.FIRE_HYDRANT, item)
        item["extras"]["substance"] = "wastewater"
        yield item
