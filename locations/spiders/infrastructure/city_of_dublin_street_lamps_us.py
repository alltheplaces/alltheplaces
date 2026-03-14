from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDublinStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "city_of_dublin_street_lamps_us"
    item_attributes = {
        "operator": "City of Dublin",
        "operator_wikidata": "Q111367157",
        "state": "OH",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "NqY8dnPSEdMJhuRw/arcgis"
    service_id = "Street_Lights"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item.get("geometry") is None:
            return
        item["ref"] = str(feature.get("OBJECTID"))
        apply_category(Categories.STREET_LAMP, item)
        item["extras"]["alt_ref"] = str(feature["FEATURE_ID"])
        if height_ft := feature["HEIGHT"]:
            item["extras"]["height"] = f"{height_ft} '"
        if model := feature["ExistingLuminaire"]:
            item["extras"]["model"] = model
        yield item
