from typing import Iterable

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NzAddressesSpider(ArcGISFeatureServerSpider, AddressSpider):
    name = "nz_addresses"
    host = "services.arcgis.com"
    context_path = "xdsHIIxuCWByZiCB/ArcGIS"
    service_id = "LINZ_NZ_Addresses"
    layer_id = "0"
    field_names = [
        "address_id",
        "full_address",
        "unit",
        "address_number",
        "address_number_suffix",
        "address_number_high",
        "road_name",
        "road_name_type",
        "road_name_suffix",
        "suburb_locality",
        "town_city",
        "address_lifecycle",
    ]
    item_attributes = {"country": "NZ"}
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Toitū Te Whenua Land Information New Zealand",
        "attribution:website": "https://linz.maps.arcgis.com/home/item.html?id=3632c8130f034ff8bbfb122a50533550;https://www.linz.govt.nz/copyright",
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("address_lifecycle") != "Current":
            # Address is probably "Proposed". Ignore.
            return

        item["ref"] = str(feature["address_id"])

        if unit_number := feature.get("unit"):
            item["extras"]["addr:unit"] = f"{unit_number}"

        housenumber_from = feature.get("address_number")
        if housenumber_from_suffix := feature.get("address_number_suffix"):
            housenumber_from = f"{housenumber_from}{housenumber_from_suffix}"
        else:
            housenumber_from = f"{housenumber_from}"
        if housenumber_to := feature.get("address_number_high"):
            housenumber_to = f"{housenumber_to}"
            item["housenumber"] = f"{housenumber_from}-{housenumber_to}"
        else:
            item["housenumber"] = f"{housenumber_from}"

        street_name = feature.get("road_name")
        street_type = feature.get("road_name_type")
        street_suffix = feature.get("road_name_suffix")
        item["street"] = " ".join(filter(None, [street_name, street_type, street_suffix]))

        if locality := feature.get("suburb_locality"):
            item["city"] = f"{locality}"
        elif city := feature.get("town_city"):
            item["city"] = f"{city}"

        item["addr_full"] = feature.get("full_address")

        yield item
