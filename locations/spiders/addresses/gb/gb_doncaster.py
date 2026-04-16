import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbDoncasterSpider(OwenBaseSpider):
    name = "gb_doncaster"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # City of Doncaster Council, address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1yeRNbG9rb-5k2GIE38JZHE4NnpzsFzcZ"
    csv_filename = "DONCASTER_CTBANDS_OSOU_202602.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
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
        return spider

    def parse_row(self, item: Feature, addr: dict):
        if m := self._re.match(
            addr["ADDR"].replace(", Donaster", ", Doncaster"),  # :)
        ):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()

            if item["city"] in ("Bawtry", "Finningley", "Mexborough", "Moss"):
                item["extras"]["addr:suburb"] = item["city"]
                item["city"] = "Doncaster"
        else:
            item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])
