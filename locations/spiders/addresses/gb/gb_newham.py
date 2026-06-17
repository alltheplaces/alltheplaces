from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbNewhamSpider(OwenBaseSpider):
    name = "gb_newham"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1mbiSoXDHnCLCxXYu3LrqXNQC7TiGxlb1"
    csv_filename = "NEWHAM_CTBANDS_ONSUD_202512.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["street_address"] = addr["ADDR"].removesuffix(", London")
        item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])
        item["city"] = "London"
