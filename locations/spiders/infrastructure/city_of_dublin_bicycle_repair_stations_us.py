from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDublinBicycleRepairStationsUSSpider(ArcGISFeatureServerSpider):
    name = "city_of_dublin_bicycle_repair_stations_us"
    item_attributes = {"operator": "City of Dublin", "operator_wikidata": "Q111367157", "state": "OH", "nsi_id": "N/A"}
    host = "services1.arcgis.com"
    context_path = "NqY8dnPSEdMJhuRw/arcgis"
    service_id = "Bike_Fix-It_Stations"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["FacilityID"])
        if located_in_name := feature.get("Location"):
            item["located_in"] = located_in_name
        apply_category(Categories.BICYCLE_REPAIR_STATION, item)
        yield item
