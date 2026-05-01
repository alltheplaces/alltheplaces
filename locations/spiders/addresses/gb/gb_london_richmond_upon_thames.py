from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbLondonRichmondUponThamesSpider(OwenBaseSpider):
    name = "gb_london_richmond_upon_thames"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1qZBK8PWCnqPhJGUwfdr7mnGpLjiEAix-"
    csv_filename = "RICHMOND_CTBANDS_ONSUD_202512.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["addr_full"] = addr["ADDR"]
