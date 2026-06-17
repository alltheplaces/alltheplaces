import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbBroadlandSpider(OwenBaseSpider):
    name = "gb_broadland"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1F47BIzLi2CDTaYiLZcWmS_xxsOskCsqm"
    csv_filename = "BROADLAND_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "Acle",
                        "Aylsham",
                        "Blofield",
                        "Brundall",
                        "Cawston",
                        "Coltishall",
                        "Drayton",
                        "Hellesdon",
                        "Horsford",
                        "Lingwood",
                        "Little Plumstead",
                        "Old Catton",
                        "Rackheath",
                        "Reepham",
                        "Spixworth",
                        "Sprowston",
                        "Taverham",
                        "Thorpe St Andrew",
                    ]
                ),
                "|".join(["Dereham", "Norwich", "Great Yarmouth"]),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR"]])
            .removesuffix(", Norfolk")
            .removesuffix(", Norolk")
            .replace(", Thorpe St Andrews", ", Thorpe St Andrew")
            .replace(", Thorpe St. Andrew", ", Thorpe St Andrew")
            .replace(", Thorpe St.andrew", ", Thorpe St Andrew")
            .replace(" Gt Yarmouth", ", Great Yarmouth")
        )
        if addr_str.endswith(", Blofield") or addr_str.endswith(", Acle"):
            addr_str += ", Norwich"
        elif addr_str.endswith(", Eastgate Cawston"):
            addr_str = addr_str.replace(", Eastgate Cawston", ", Eastgate, Cawston, Norwich")

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
