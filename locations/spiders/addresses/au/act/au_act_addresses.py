from typing import Iterable

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuActAddressesSpider(ArcGISFeatureServerSpider, AddressSpider):
    name = "au_act_addresses"
    host = "services1.arcgis.com"
    context_path = "E5n4f1VY84i0xSjy/ArcGIS"
    service_id = "ACTGOV_ADDRESSES"
    layer_id = "0"
    field_names = [
        "DIVISION",
        "DOOR_NO",
        "ADDRESS_ID",
        "STREET_NUMBER",
        "STREET_NAME",
        "STREET_TYPE",
    ]
    item_attributes = {"state": "ACT", "country": "AU"}
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Australian Capital Territory",
        "attribution:website": "https://www.arcgis.com/sharing/rest/content/items/13427dc77da340a29dd6601af4d7484d/info/metadata/metadata.xml?format=default&output=html",
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["ADDRESS_ID"])

        if unit_number := feature.get("DOOR_NO"):
            item["extras"]["addr:unit"] = f"{unit_number}"

        item["housenumber"] = feature["STREET_NUMBER"]

        street_name = feature.get("STREET_NAME")
        if street_type := feature.get("STREET_TYPE"):
            item["street"] = f"{street_name} {street_type}"
        else:
            item["street"] = f"{street_name}"

        item["city"] = feature["DIVISION"]

        yield item
