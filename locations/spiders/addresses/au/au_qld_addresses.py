from typing import Iterable

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuQldAddressesSpider(ArcGISFeatureServerSpider, AddressSpider):
    name = "au_qld_addresses"
    host = "spatial-gis.information.qld.gov.au"
    context_path = "arcgis"
    service_id = "PlanningCadastre/LandParcelPropertyFramework"
    server_type = "MapServer"
    layer_id = "0"
    field_names = [
        "address_pid",
        "unit_number",
        "unit_suffix",
        "floor_number",
        "street_number",
        "street_full",
        "locality",
        "address",
    ]
    item_attributes = {"state": "QLD", "country": "AU"}
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "State of Queensland",
        "attribution:website": "https://qldspatial.information.qld.gov.au/catalogue/custom/viewMetadataDetails.page?uuid=%7BF878C43D-3087-4102-8F28-1CFEA49B34F1%7D",
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["address_pid"])

        if unit_number := feature.get("unit_number"):
            if unit_suffix := feature.get("unit_suffix"):
                item["extras"]["addr:unit"] = f"{unit_number}{unit_suffix}"
            else:
                item["extras"]["addr:unit"] = f"{unit_number}"

        if floor_number := feature.get("floor_number"):
            item["extras"]["addr:floor"] = f"{floor_number}"

        item["housenumber"] = feature["street_number"]
        item["street"] = feature["street_full"]
        item["city"] = feature["locality"]
        item["addr_full"] = feature["address"]

        yield item
