import csv
from io import BytesIO, TextIOWrapper
from typing import Any
from zipfile import ZipFile

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines


class GbSouthamptonSpider(AddressSpider):
    name = "gb_southampton"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information provided by Southampton City Council and licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 60 * 5}
    no_refs = True
    start_urls = [
        "https://drive.usercontent.google.com/download?id=1JyJpK88jf80Tqzn4qBr6m7nwTtK9CJyX&export=download&confirm=t"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        with ZipFile(BytesIO(response.body)) as zip_file:
            for addr in csv.DictReader(
                TextIOWrapper(zip_file.open("SOUTHAMPTON_CTBANDS_OSOU_202602.csv"), encoding="utf-8")
            ):
                item = Feature()
                item["ref"] = addr["PROPREF"]
                item["extras"]["ref:GB:uprn"] = addr["UPRN"]
                item["lat"] = addr["LAT"]
                item["lon"] = addr["LNG"]
                item["postcode"] = addr["POSTCODE"]

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
                item["country"] = "GB"

                yield item
