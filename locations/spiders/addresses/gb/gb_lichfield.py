from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbLichfieldSpider(OwenBaseSpider):
    name = "gb_lichfield"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Council Tax bands of properties in the Lichfield area, (c) Lichfield District Council, 2025. This information is licensed under the terms of the Open Government Licence."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "11jzD3zSRpLYP1QOXYclDSQr5C7bIsPRs"
    csv_filename = "LDC_CTBANDS_NSUL_202501.csv"

    def parse_row(self, item: Feature, addr: dict):
        street_address = []
        for component in addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]:
            if component not in [
                "",
                "Staffs",
                "Staffs.",
                "Burton On Trent",
                "West Midlands",
                "Sutton Coldfield",
                "Lichfield",
            ]:
                street_address.append(component)

        item["street_address"] = " ".join(street_address)
