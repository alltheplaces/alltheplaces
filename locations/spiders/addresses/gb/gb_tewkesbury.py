import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbTewkesburySpider(OwenBaseSpider):
    name = "gb_tewkesbury"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1Nqgl_rxicohjFwIUf7hR9hI2_HeMi_09"
    csv_filename = "TEWKESBURY_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "ALDERTON",
                        "ASHCHURCH",
                        "ASHCHURCH GARDENS",
                        "BADGEWORTH",
                        "BISHOPS CLEEVE",
                        "BROCKWORTH",
                        "CHURCHDOWN",
                        "DUMBLETON",
                        "GOTHERINGTON",
                        "GREET",
                        "HIGHNAM",
                        "HUCCLECOTE",
                        "INNSWORTH",
                        "LONGFORD",
                        "MINSTERWORTH",
                        "MITTON",
                        "NORTHWAY",
                        "NORTON",
                        "SANDHURST",
                        "SHURDINGTON",
                        "STOKE ORCHARD",
                        "TWIGWORTH",
                        "TWYNING",
                        "WALTON CARDIFF",
                        "WINCHCOMBE",
                        "WOODMANCOTE",
                    ]
                ),
                "|".join(["BROADWAY", "CHELTENHAM", "EVESHAM", "GLOUCESTER", "MORETON IN MARSH", "TEWKESBURY"]),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"], addr["ADDR5"]])
            .removesuffix("WORCS")
            .removesuffix("WORCESTERSHIRE")
            .removesuffix("GLOS")
            .removesuffix("GLOUCESTERSHIRE")
            .strip("., ")
            .replace(", .,", ",")
            .replace(", CHELTENHAM GLOUCESTER", ", CHELTENHAM")
            .replace(", CHELTNEHAM", ", CHELTENHAM")
            .replace(", CHELLTENHA", ", CHELTENHAM")
            .replace(", CHELTENHAN", ", CHELTENHAM")
            .replace(", CHELTLENHAM", ", CHELTENHAM")
            .replace(", CHURHDOWN", ", CHURCHDOWN")
            .replace(", CHURCHDOWN GLS", ", CHURCHDOWN")
            .replace(", GLOCESTER", ", GLOUCESTER")
            .replace(", GLOUCETSER", ", GLOUCESTER")
            .replace(", TEWKEBSURY", ", TEWKESBURY")
            .replace(", TEWKESBRY", ", TEWKESBURY")
            .replace(", TEWKKESBURY", ", TEWKESBURY")
            .replace(", TEWKSBURY", ", TEWKESBURY")
        )

        if (
            addr_str.endswith(", INNSWORTH")
            or addr_str.endswith(", CHURCHDOWN")
            or addr_str.endswith(", NORTON")
            or addr_str.endswith(", SANDHURST")
            or addr_str.endswith(", MINSTERWORTH")
            or addr_str.endswith(", GREET")
        ):
            addr_str += ", GLOUCESTER"
        elif addr_str.endswith(", BISHOPS CLEEVE"):
            addr_str += ", CHELTENHAM"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
