from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbNorwichSpider(OwenBaseSpider):
    name = "gb_norwich"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1FaalTncbWE0KaaMKTyVI9hvX12yoCpbF"
    csv_filename = "NORWICH_CTBANDS_OSOU_202604.csv"

    def parse_row(self, item: Feature, addr: dict):
        if addr["ADDR1"].isdigit():
            item["housenumber"] = addr["ADDR1"]
        elif addr["ADDR1"]:
            item["street_address"] = merge_address_lines([addr["ADDR1"], addr["ADDR2"]])
        item["street"] = addr["ADDR2"]
        item["city"] = addr["ADDR3"]
