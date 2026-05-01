from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbHackneySpider(OwenBaseSpider):
    name = "gb_hackney"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Council tax bands of all properties in the London Borough of Hackney, (c) London Borough of Hackney, 2025. This information is licensed under the terms of the Open Government Licence."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "16B9vV-ERcfW4B--YN7FpdmqjUDKchG4Z"
    csv_filename = "HACKNEY_CTBANDS_ONSUD_202507.csv"

    def parse_row(self, item: Feature, addr: dict):
        street_address = []
        for component in addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]:
            if component not in ["", "LONDON", "HACKNEY"]:
                street_address.append(component)

        item["street_address"] = " ".join(street_address)
        item["extras"]["addr:suburb"] = "Hackney"
        item["city"] = "London"
