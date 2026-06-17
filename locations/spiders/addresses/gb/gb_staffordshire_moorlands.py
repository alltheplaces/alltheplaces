from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbStaffordshireMoorlandsSpider(OwenBaseSpider):
    name = "gb_staffordshire_moorlands"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information provided by Staffordshire Moorlands District Council and licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1dQp-aMAF57OTmjglCvCa2GDbo2XQ6ViD"
    csv_filename = "STAFFSMOORLANDS_CTBANDS_OSOU_202604.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["addr_full"] = merge_address_lines(
            [
                addr["ADDR1"],
                addr["ADDR2"],
                addr["ADDR3"],
                addr["ADDR4"],
                addr["ADDR5"],
                item.get("postcode"),
            ]
        )
