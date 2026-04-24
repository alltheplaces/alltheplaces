from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbHaringeySpider(OwenBaseSpider):
    name = "gb_haringey"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1y4Kbq4P99L5oipwjxC34CcSb-l7skL48"
    csv_filename = "HARINGEY_CTBANDS_OSOU_202601.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["street_address"] = addr["ADDRESS"].removesuffix(", London")
        item["city"] = "London"
