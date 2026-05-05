import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbNeathPortTalbotSpider(OwenBaseSpider):
    name = "gb_neath_port_talbot"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        # Address strings are released without restrictions
        "attribution:name": "Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1Icsy6racdB3yC3NkWq9i5taN_HV3aa_y"
    csv_filename = "NEATHPORTTALBOT_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?(?:, ({}))(?:, (?:DYFED|GLAM))?$".format(
                "|".join(
                    [
                        "ABERAFAN",
                        "ABERAVON",
                        "ABERDULAIS",
                        "ABERGWYNFI",
                        "ALLTWEN",
                        "BAGLAN MOORS",
                        "BAGLAN",
                        "BANWEN",
                        "BLAENGWYNFI",
                        "BRITON FERRY",
                        "BRYN",
                        "BRYNAMMAN",
                        "BRYNCOCH",
                        "CADOXTON",
                        "CAEWERN",
                        "CILFREW",
                        "CILMAENGWYN",
                        "CIMLA",
                        "CLYNE",
                        "COED DARCY",
                        "COURT HERBERT",
                        "CRYMLYN BURROWS",
                        "CRYNANT",
                        "CWMAFAN",
                        "CWMAVON",
                        "CWMGORS",
                        "CWMGWRACH",
                        "CWMLLYNFELL",
                        "CYMMER",
                        "DUFFRYN RHONDDA",
                        "GELLIGRON",
                        "GLYNCORRWG",
                        "GLYNNEATH",
                        "GODRE'R GRAIG",
                        "GOYTRE",
                        "GWAUNCAEGURWEN",
                        "JERSEY MARINE",
                        "LLANDARCY",
                        "LONGFORD",
                        "MARGAM",
                        "MELINCOURT",
                        "NEATH ABBEY",
                        "ONLLWYN",
                        "PONTRHYDYFEN",
                        "RESOLVEN",
                        "RHIWFAWR",
                        "RHOS",
                        "RHYDDINGS",
                        "SANDFIELDS",
                        "SEVEN SISTERS",
                        "SKEWEN",
                        "TAIBACH",
                        "TAIRGWAITH",
                        "TONMAWR",
                        "TONNA",
                        "TREBANOS",
                        "VELINDRE",
                        "WAUNCEIRCH",
                        "YSTALYFERA",
                    ]
                ),
                "|".join(
                    [
                        "NEATH",
                        "PORT TALBOT",
                        "SWANSEA",
                        "AMMANFORD",
                        "PONTARDAWE",
                        "NEAR BRIDGEND",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]])
            .replace(", SWANSEWA", ", SWANSEA")
            .replace(", SWANEA", ", SWANSEA")
            .replace(", PORTTALBOT", ", PORT TALBOT")
            .replace(", PONTARDAWE SWANSEA", ", PONTARDAWE")
            .replace(", PONTARDAWE, SWANSEA", ", PONTARDAWE")
            .replace(", FABIAN WAY CRYMLYN BURROWS", ", FABIAN WAY, CRYMLYN BURROWS")
            .replace(", GWAUN CAE GURWEN", ", GWAUNCAEGURWEN")
            .replace(", GODRERGRAIG", "GODRE'R GRAIG")
        )

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
