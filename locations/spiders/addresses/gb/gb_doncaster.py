import csv
import re
from io import BytesIO, TextIOWrapper
from typing import Any
from zipfile import ZipFile

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines


class GbDoncasterSpider(AddressSpider):
    name = "gb_doncaster"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # City of Doncaster Council, address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 60 * 5}
    no_refs = True
    start_urls = [
        "https://drive.usercontent.google.com/download?id=1yeRNbG9rb-5k2GIE38JZHE4NnpzsFzcZ&export=download&confirm=t"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        _re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})(?:, South Yorkshire|, S Yorks|, S Yorkshire|, East Yorkshire)?$".format(
                "|".join(
                    [
                        # "suburbs"
                        "Adwick Le Street",
                        "Arksey",
                        "Armthorpe",
                        "Askern",
                        "Auckley",
                        "Austerfield",
                        "Balby",
                        "Barnburgh",
                        "Barnby Dun",
                        "Bawtry",
                        "Bentley",
                        "Bessacarr",
                        "Blaxton",
                        "Braithwell",
                        "Branton",
                        "Campsall",
                        "Cantley",
                        "Carcroft",
                        "Clifton",
                        "Conisbrough",
                        "Cusworth",
                        "Denaby Main",
                        "Dunscroft",
                        "Dunsville",
                        "Edenthorpe",
                        "Edlington",
                        "Finningley",
                        "Fishlake",
                        "Harlington",
                        "Hatfield Woodhouse",
                        "Hatfield",
                        "Highfields",
                        "Mexborough",
                        "Moorends",
                        "Moss",
                        "New Rossington",
                        "Norton",
                        "Rossington",
                        "Scawsby",
                        "Scawthorpe",
                        "Skellow",
                        "Sprotbrough",
                        "Stainforth",
                        "Sunnyfields",
                        "Sykehouse",
                        "Thorne",
                        "Tickhill",
                        "Toll Bar",
                        "Wadworth",
                        "Warmsworth",
                        "Woodlands",
                        "Kirk Sandall",
                    ]
                ),
                "|".join(
                    [
                        # These aren't "cities", but are missing cities from the source data, handled in code lower.
                        "Bawtry",
                        "Finningley",
                        "Mexborough",
                        "Moss",
                        # cities
                        "Barnsley",
                        "Doncaster",
                        "Goole",
                        "Pontefract",
                        "Rotherham",
                        "Wakefield",
                    ]
                ),
            )
        )

        with ZipFile(BytesIO(response.body)) as zip_file:
            for addr in csv.DictReader(
                TextIOWrapper(zip_file.open("DONCASTER_CTBANDS_OSOU_202602.csv"), encoding="utf-8")
            ):
                item = Feature()
                item["ref"] = addr["PROPREF"]
                item["extras"]["ref:GB:uprn"] = addr["UPRN"]
                item["lat"] = addr["LAT"]
                item["lon"] = addr["LNG"]
                item["postcode"] = addr["POSTCODE"]

                if m := _re.match(
                    addr["ADDR"].replace(", Donaster", ", Doncaster"),  # :)
                ):
                    item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()

                    if item["city"] in ("Bawtry", "Finningley", "Mexborough", "Moss"):
                        item["extras"]["addr:suburb"] = item["city"]
                        item["city"] = "Doncaster"
                else:
                    item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])

                item["country"] = "GB"

                yield item
