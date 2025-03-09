from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BarwonWaterPotablePumpStationsAUSpider(ArcGISFeatureServerSpider):
    name = "barwon_water_potable_pump_stations_au"
    item_attributes = {"operator": "Barwon Water", "operator_wikidata": "Q4865988"}
    host = "services8.arcgis.com"
    context_path = "uLK1YQYKdEhgFHsx/ArcGIS"
    service_id = "Barwon_Water_Water_Assets"
    layer_id = "0"
    where_query = "NODE_TYPE = 'PS'"  # PS = Pump Station

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["BW_ASSET_ID"])
        item["name"] = feature.get("GENERAL_TEXT")
        apply_category(Categories.PUMPING_STATION_WATER, item)
        yield item
