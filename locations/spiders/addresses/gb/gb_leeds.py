from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbLeedsSpider(OwenBaseSpider):
    name = "gb_leeds"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Council tax bands of all properties in Leeds, (c) Leeds City Council, 2024. This information is licensed under the terms of the Open Government Licence."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1-goEmDTjb1h3K9nMIkChA-Be6CDMMcSm"
    csv_filename = "LEEDS_CTBANDS_ONSUD_2024.csv"

    def parse_row(self, item: Feature, addr: dict):
        street_address = []
        for component in addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]:
            if component not in ["", "LEEDS"]:
                street_address.append(component)

        item["street_address"] = " ".join(street_address)
