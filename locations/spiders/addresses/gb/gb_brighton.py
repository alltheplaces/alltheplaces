from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbBrightonSpider(OwenBaseSpider):
    name = "gb_brighton"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information from Brighton & Hove City Council licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0"
    }

    drive_id = "1ElqOPZ8OCF0oTjNYxD0ORBwsbCzTmm7C"
    csv_filename = "BH_CTBANDS_ONSUD_202511.csv"

    def parse_row(self, item: Feature, addr: dict):
        street_address = []
        for component in addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"], addr["ADDR5"]:
            component = component.strip()

            if not component:
                continue

            if component.endswith("LONDON ROAD BRIGHTON"):
                item["city"] = "Brighton"
                component = component.removesuffix(" BRIGHTON")
            if component.endswith("MARINE VIEW BRIGHTON"):
                item["city"] = "Brighton"
                component = component.removesuffix(" BRIGHTON")

            if component in ["BRIGHTON", "HOVE"]:
                item["city"] = component.title()
            elif component in [
                "WOODINGDEAN BRIGHTON",
                "COLDEAN BRIGHTON",
                "PATCHAM BRIGHTON",
                "BEVENDEAN BRIGHTON",
            ]:
                item["extras"]["addr:suburb"] = component.split(" ", 1)[0].title()
                item["city"] = "Brighton"
            elif component in ["PORTSLADE", "SALTDEAN", "FALMER", "ROTTINGDEAN", "OVINGDEAN", "WOODINGDEAN"]:
                item["extras"]["addr:suburb"] = component.title()
            else:
                street_address.append(component)

        item["street_address"] = merge_address_lines(street_address)
