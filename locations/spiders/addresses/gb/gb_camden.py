from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbCamdenSpider(OwenBaseSpider):
    name = "gb_camden"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1LHisoJEM7uXW4eodddV1-X9Oac0u-aS3"
    csv_filename = "CAMDEN_CTBANDS_ONSUD_202511.csv"

    def parse_row(self, item: Feature, addr: dict):
        street_address = []
        for component in addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"], addr["ADDR5"]:
            if component not in ["", "LONDON", "GREATER LONDON", "CAMDEN"]:
                street_address.append(component)

        item["street_address"] = ", ".join(street_address)
        item["extras"]["addr:suburb"] = "Camden"
        item["city"] = "London"
