from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDublinStreetCabinetsUSSpider(ArcGISFeatureServerSpider):
    name = "city_of_dublin_street_cabinets_us"
    item_attributes = {
        "operator": "City of Dublin",
        "operator_wikidata": "Q111367157",
        "state": "OH",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "NqY8dnPSEdMJhuRw/arcgis"
    service_id = "Street_Light_Controllers"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item.get("geometry") is None:
            return
        item["ref"] = feature["FacilityID"]
        item["street_address"] = feature["ADDRESS"]
        item.pop("addr_full", None)
        apply_category(Categories.STREET_CABINET_LIGHTING, item)
        if voltage_v := feature.get("VOLTAGE"):
            item["extras"]["voltage"] = f"{voltage_v}"
        yield item
