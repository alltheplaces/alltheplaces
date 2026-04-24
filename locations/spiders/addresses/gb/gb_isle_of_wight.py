import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbIsleOfWightSpider(OwenBaseSpider):
    name = "gb_osle_of_wight"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1S4cnJIkelcmqwJwok5yDzw8O1T-ltMXY"
    csv_filename = "ISLE_OF_WIGHT_CTBANDS_ONSUD_202512.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "Alverstone",
                        "Alverstone Garden Village",
                        "Apse Heath",
                        "Arreton",
                        "Atherfield",
                        "Barton",
                        "Binfield",
                        "Binstead",
                        "Bonchurch",
                        "Bouldnor",
                        "Brading",
                        "Brighstone",
                        "Brook",
                        "Calbourne",
                        "Camphill",
                        "Carisbrooke",
                        "Chale",
                        "Chale Green",
                        "Chillerton",
                        "Cranmore",
                        "Godshill",
                        "Gunville",
                        "Gurnard",
                        "Havenstreet",
                        "Haylands",
                        "Lake",
                        "Luccombe",
                        "Merstone",
                        "Newbridge",
                        "Newchurch",
                        "Ningwood",
                        "Niton",
                        "Niton Undercliff",
                        "Northwood",
                        "Norton",
                        "Oakfield",
                        "Parkhurst",
                        "Pondwell",
                        "Porchfield",
                        "Rookley",
                        "Sandford",
                        "Shalfleet",
                        "Shorwell",
                        "St Helens",
                        "St Lawrence",
                        "Thorley",
                        "Wellow",
                        "Whippingham",
                        "Whiteley Bank",
                        "Whitwell",
                        "Winford",
                        "Wootton Bridge",
                        "Wroxall",
                    ]
                ),
                "|".join(
                    [
                        "Bembridge",
                        "Branstone",
                        "Cowes",
                        "East Cowes",
                        "Freshwater",
                        "Newport",
                        "Ryde",
                        "Sandown",
                        "Seaview",
                        "Shanklin",
                        "Totland Bay",
                        "Ventnor",
                        "Yarmouth",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = merge_address_lines([addr["ADDR"]]).removesuffix(", Isle Of Wight")
        if addr_str.endswith(", Chillerton") or addr_str.endswith(", Shalfleet"):
            addr_str += ", Newport"
        elif addr_str.endswith(", Whitwell") or addr_str.endswith(", Niton"):
            addr_str += ", Ventnor"
        elif addr_str.endswith(", Gurnard"):
            addr_str += ", Cowes"
        elif addr_str.endswith(", Lake"):
            addr_str += ", Sandown"
        elif addr_str.endswith(", Totland"):
            addr_str = addr_str.replace(", Totland", ", Totland Bay")

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = addr_str

        item["extras"]["addr:county"] = "Isle of Wight"
