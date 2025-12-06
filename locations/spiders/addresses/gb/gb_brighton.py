import csv
from io import BytesIO, TextIOWrapper
from typing import Any
from zipfile import ZipFile

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines

# This data has been acquired by Owen Boswarva via a FoI request, unfortunately it will likely not be updated.
# https://www.owenboswarva.com/blog/post-addr26.htm


class GbBrightonSpider(AddressSpider):
    name = "gb_brighton"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information from Brighton & Hove City Council licensed under the Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2025. Contains Royal Mail data © Royal Mail copyright and Database right. Contains GeoPlace data © Local Government Information House Limited copyright and database right. Office for National Statistics licensed under the Open Government Licence v.3.0"
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 60 * 5}
    no_refs = True
    start_urls = [
        "https://drive.usercontent.google.com/download?id=1ElqOPZ8OCF0oTjNYxD0ORBwsbCzTmm7C&export=download&confirm=t"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        with ZipFile(BytesIO(response.body)) as zip_file:
            for addr in csv.DictReader(TextIOWrapper(zip_file.open("BH_CTBANDS_ONSUD_202511.csv"), encoding="utf-8")):
                item = Feature()
                item["ref"] = addr["PROPREF"]
                item["extras"]["ref:GB:uprn"] = addr["UPRN"]
                item["lat"] = addr["LAT"]
                item["lon"] = addr["LNG"]
                item["postcode"] = addr["POSTCODE"]
                item["country"] = "GB"

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

                yield item
