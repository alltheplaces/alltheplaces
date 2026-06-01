from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbSouthwarkSpider(OwenBaseSpider):
    name = "gb_southwark"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1xdOUUFVUkHW366FGAsaGGUXc3yCwZ-S8"
    csv_filename = "SOUTHWARK_CTBANDS_ONSUD_202512.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["street_address"] = addr["ADDR"].removesuffix(", London")
        item["city"] = "London"
