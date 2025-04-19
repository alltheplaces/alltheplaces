from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfOttawaStreetLampsCASpider(ArcGISFeatureServerSpider):
    name = "city_of_ottawa_street_lamps_ca"
    item_attributes = {"operator": "City of Ottawa", "operator_wikidata": "Q5123850", "state": "ON"}
    host = "maps.ottawa.ca"
    context_path = "arcgis"
    service_id = "Streets"
    server_type = "MapServer"
    layer_id = "14"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["GLOBALID"].strip("{}")
        if street_name := feature.get("STREET_NAM"):
            item["street"] = street_name
        apply_category(Categories.STREET_LAMP, item)
        if height_m := feature.get("POLE_HEIGHT"):
            item["extras"]["height"] = f"{height_m} m"
        yield item
