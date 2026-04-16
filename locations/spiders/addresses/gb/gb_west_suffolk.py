from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GBWestSuffolkSpider(OwenBaseSpider):
    name = "gb_west_suffolk"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "© West Suffolk Council, 2026. Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1WdTFLQ8OAJfDoJWhcdFSNWqhMCTkw7iH"
    csv_filename = "WESTSUFFOLK_CTBANDS_OSOU_202602.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["extras"]["ref:GB:uprn"] = addr["UPRN              "]
        item["addr_full"] = merge_address_lines(
            [addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"], item.get("postcode")]
        )
