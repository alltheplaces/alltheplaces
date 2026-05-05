from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuVicAddressesSpider(ArcGISFeatureServerSpider, AddressSpider):
    name = "au_vic_addresses"
    host = "services-ap1.arcgis.com"
    context_path = "P744lA0wf4LlBZ84/ArcGIS"
    service_id = "Vicmap_Address"
    layer_id = "0"
    field_names = [
        "ezi_address",
        "locality_name",
        "num_address",
        "num_road_address",
        "pfi",
        "postcode",
        "road_name",
        "road_type",
        "source_verified",
    ]
    item_attributes = {"state": "VIC", "country": "AU"}
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "State of Victoria",
        "attribution:website": "https://www.vic.gov.au/dtp-website-terms-and-conditions#copyright",
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("num_address") is None:
            # Features without a housenumber should be ignored.
            return

        item["ref"] = feature["pfi"]

        # num_address may take multiple forms including examples:
        #  99
        #  1/99
        #  1A/99
        #  1-1A/99
        #  1-3/99
        #  90-99
        #  90-90A
        #  1/90-99
        #  1A/90-99
        #  1-1A/90-99
        #  1-3/90-99
        num_address = feature["num_address"]
        if "/" in num_address:
            flats, housenumbers = feature["num_address"].split("/", 1)
            # Single housenumber or range of housenumbers
            item["housenumber"] = housenumbers
            if "-" in flats:
                # Single address for a collection of units/"flats".
                item["extras"]["addr:flats"] = flats
            else:
                # Single address for a single unit.
                item["extras"]["addr:unit"] = flats
        else:
            # Single housenumber or range of housenumbers. No flats/units.
            item["housenumber"] = num_address

        road_name = feature.get("road_name")
        if road_type := feature.get("road_type"):
            item["street"] = " ".join([road_name, road_type])
        else:
            # Not all streets have a suffix (e.g. "10 The Esplanade")
            item["street"] = road_name

        item["city"] = feature["locality_name"]
        item["postcode"] = feature["postcode"]

        item["street_address"] = feature["num_road_address"]
        item["addr_full"] = feature["ezi_address"]

        if source_verified := feature.get("source_verified"):
            verification_timestamp = datetime.fromtimestamp(int(float(source_verified) / 1000), UTC)
            item["extras"]["source:date"] = verification_timestamp.isoformat()

        yield item
