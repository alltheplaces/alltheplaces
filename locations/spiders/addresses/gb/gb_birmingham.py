from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbBirminghamSpider(OwenBaseSpider):
    name = "gb_birmingham"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "11mFnqYnXW_cNRrKeppIsIgMOs9A52VUa"
    csv_filename = "BHAM_CTBANDS_NSUL_202501.csv"

    def parse_row(self, item: Feature, addr: dict):
        street_address = []
        for component in addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]:
            if component not in ["", "Birmingham", "Coldfield"]:
                street_address.append(component)

        item["street_address"] = " ".join(street_address)
