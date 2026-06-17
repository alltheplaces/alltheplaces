from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbDurhamSpider(OwenBaseSpider):
    name = "gb_durham"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Council tax data, (c) Durham County Council, 2025. This information is licensed under the terms of the Open Government Licence."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1biAJJ8P9TaX0WJhvE_2Yky6aHemktJ08"
    csv_filename = "DURHAM_CTBANDS_ONSUD_202510.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["addr_full"] = merge_address_lines(
            [
                addr["ADDR1"],
                addr["ADDR2"],
                addr["ADDR3"],
                addr["ADDR4"],
                addr["ADDR4"],
                addr["ADDR5"],
                item.get("postcode"),
            ]
        )
