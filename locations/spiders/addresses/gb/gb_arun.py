import csv
import re
from io import BytesIO, TextIOWrapper
from typing import Any
from zipfile import ZipFile

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses


class GbArunSpider(AddressSpider):
    name = "gb_arun"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 60 * 5}
    no_refs = True
    start_urls = [
        "https://drive.usercontent.google.com/download?id=1030scDO9gFByATcXGQK5Ao7m9pTYW5Xs&export=download&confirm=t"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        _re = re.compile(
            r"^(.+?)(?:, ({}))?(?:, ({}))?(?:,? West Sussex)?$".format(
                "|".join(
                    [
                        # "suburbs"
                        "Pagham",
                        "Bersted",
                        "Rustington",
                        "East Preston",
                        "Angmering",
                        "Wick",
                        "Yapton",
                        "Middleton-On-Sea",
                        "Barnham",
                        "Felpham",
                        "Eastergate",
                        "Findon",
                        "Walberton",
                        "Westergate",
                        "Fontwell",
                        "Ferring",
                        "Climping",
                        "Aldingbourne",
                        "Tortington",
                        "Middleton On Sea",
                        "Clapham",
                        "Slindon",
                        "Slindon Common",
                        "Patching",
                        "Poling",
                        "Burpham",
                        "Ford",
                        "Aldwick",
                        "Woodgate",
                    ]
                ),
                "|".join(
                    [
                        # cities
                        "Arundel",
                        "Barnham",
                        "Bognor Regis",
                        "Chichester",
                        "Littlehampton",
                        "Nr Bognor Regis",
                        "Worthing",
                        "Madehurst",
                    ]
                ),
            )
        )

        with ZipFile(BytesIO(response.body)) as zip_file:
            for addr in csv.DictReader(TextIOWrapper(zip_file.open("ARUN_CTBANDS_OSOU_202602.csv"), encoding="utf-8")):
                item = Feature()
                item["ref"] = addr["PROPREF"]
                item["extras"]["ref:GB:uprn"] = addr["UPRN"]
                item["lat"] = addr["LAT"]
                item["lon"] = addr["LNG"]
                item["postcode"] = addr["POSTCODE"]

                if m := _re.match(addr["ADDR"]):
                    item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()

                item["country"] = "GB"

                yield item
