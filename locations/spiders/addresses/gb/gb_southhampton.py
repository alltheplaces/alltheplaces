from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbSouthamptonSpider(OwenBaseSpider):
    name = "gb_southampton"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information provided by Southampton City Council and licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1JyJpK88jf80Tqzn4qBr6m7nwTtK9CJyX"
    csv_filename = "SOUTHAMPTON_CTBANDS_OSOU_202602.csv"

    def parse_row(self, item: Feature, addr: dict):
        item["street_address"] = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]])
            .replace(", SOUTHAMPTON, WOOLSTON", ", WOOLSTON, SOUTHAMPTON")
            .replace(", BITTERNE SOUTHAMPTON", ", BITTERNE, SOUTHAMPTON")
            .replace(", SWAYTHLING SOUTHAMPTON", ", SWAYTHLING, SOUTHAMPTON")
            .replace(", REDBRIDGE SOUTHAMPTON", ", REDBRIDGE, SOUTHAMPTON")
            .replace(", WESTON SOUTHAMPTON", ", WESTON, SOUTHAMPTON")
            .replace(", MILLBROOK SOUTHAMPTON", ", MILLBROOK, SOUTHAMPTON")
            .removesuffix(", SO14 OFN")
            .removesuffix(", SO17 2JY")
            .removesuffix(", HANTS")
            .removesuffix(", HAMPSHIRE")
            .removesuffix(", SOUTHAMPTON")
            .removesuffix(", SDOUTHAMPTON")
            .removesuffix(", SOTHAMPTON")
            .removesuffix(", SOTUHAMPTON")
            .removesuffix(", SOUTAMPTON")
            .removesuffix(", SOUTHAM[PTON")
            .removesuffix(", SOUTHAMP")
            .removesuffix(", SOUTHAMPON")
            .removesuffix(", SOUTHAMPT")
            .removesuffix(", SOUTHAMPTION")
            .removesuffix(", SOUTHAMPTN")
            .removesuffix(", SOUTHAMPTNO")
            .removesuffix(", SOUTHAMPTOIN")
            .removesuffix(", SOUTHAMPTOM")
            .removesuffix(", SOUTHAMPTON.")
            .removesuffix(", SOUTHAMPTONIN")
            .removesuffix(", SOUTHAMPTONO")
            .removesuffix(", SOUTHAMPTONT")
            .removesuffix(", SOUTHAMPTONTOIN")
            .removesuffix(", SOUTHAMPTONTON")
            .removesuffix(", SOUTHAMPTONTONOIN")
            .removesuffix(", SOUTHAMPTONTONON")
            .removesuffix(", SOUTHAMPTONTONONO")
            .removesuffix(", SOUTHAMPTPON")
            .removesuffix(", SOUTHAMTON")
            .removesuffix(", SOUTHAMTPON")
            .removesuffix(", SOUTHANPTON")
            .removesuffix(", SOUTHAPTON")
            .removesuffix(", SOUTHMPTON")
        )

        item["city"] = "Southampton"
