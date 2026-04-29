from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbAberdeenshireSpider(OwenBaseSpider):
    name = "gb_aberdeenshire"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1zSKt3EIURFP-WOmm2BLeCmuf9yBfyxkF"
    csv_filename = "ABERDEENSHIRE_CTBANDS_ONSUD_202512.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])
