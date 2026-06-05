from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BrisbaneCityCouncilParksAUSpider(ArcGISFeatureServerSpider):
    name = "brisbane_city_council_parks_au"
    item_attributes = {"operator": "Brisbane City Council", "operator_wikidata": "Q56477660", "state": "QLD"}
    host = "services2.arcgis.com"
    context_path = "dEKgZETqwmDAh1rP/ArcGIS"
    service_id = "Park_Locations"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("geometry", None)
        item["ref"] = feature["PARK_NUMBER"]
        item["name"] = feature["PARK_NAME"]
        item["lat"] = feature["LAT"]
        item["lon"] = feature["LONG"]
        item["street"] = item.pop("street_address", None)
        apply_category(Categories.LEISURE_PARK, item)
        yield item
