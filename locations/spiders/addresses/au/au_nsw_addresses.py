from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuNswAddressesSpider(ArcGISFeatureServerSpider, AddressSpider):
    name = "au_nsw_addresses"
    host = "portal.spatial.nsw.gov.au"
    context_path = "server"
    service_id = "NSW_Geocoded_Addressing_Theme"
    layer_id = "1"
    field_names = [
        "gurasid",
        "lastupdate",
        "address",
        "housenumber",
    ]
    item_attributes = {"state": "NSW", "country": "AU"}
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "State of New South Wales",
        "attribution:website": "https://www.spatial.nsw.gov.au/copyright",
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["gurasid"])

        item["housenumber"] = feature["housenumber"]
        item["addr_full"] = feature["address"]

        if last_update := feature.get("lastupdate"):
            last_update_timestamp = datetime.fromtimestamp(int(float(last_update) / 1000), UTC)
            item["extras"]["source:date"] = last_update_timestamp.isoformat()

        yield item
