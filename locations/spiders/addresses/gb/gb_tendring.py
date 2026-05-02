import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import clean_address, merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbTendringSpider(OwenBaseSpider):
    name = "gb_tendring"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1ZqA5ZUXVtjgCqAOZiz6CvdqwK47OcX6W"
    csv_filename = "TENDRING_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "Alresford",
                        "Ardleigh",
                        "Beaumont",
                        "Bradfield",
                        "Brightlingsea",
                        "Dovercourt",
                        "Elmstead",
                        "Great Bentley",
                        "Holland On Sea",
                        "Jaywick",
                        "Kirby Cross",
                        "Kirby Le Soken",
                        "Little Clacton",
                        "Little Oakley",
                        "Mistley",
                        "Parkeston",
                        "Ramsey",
                        "St Osyth",
                        "Thorpe Le Soken",
                        "Thorrington",
                        "Weeley",
                    ]
                ),
                "|".join(
                    [
                        "Brightlingsea",
                        "Clacton-on-Sea",
                        "Colchester",
                        "Frinton-on-Sea",
                        "Harwich",
                        "Manningtree",
                        "Walton-on-the-Naze",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            clean_address(addr["ADDR"])
            .removesuffix(", Essex")
            .replace(", Lawford Manningtree", ", Lawford, Manningtree")
            .replace(", St Osyth Clacton-on-Sea", ", St Osyth, Clacton-on-Sea")
            .replace(", Thorpe-Le-Soken", ", Thorpe Le Soken")
        )
        if addr_str.endswith(", Alresford") or addr_str.endswith(", Elmstead") or addr_str.endswith(", Thorrington"):
            addr_str += ", Colchester"
        elif addr_str.endswith(", Beaumont") or addr_str.endswith(", Thorpe Le Soken"):
            addr_str += ", Clacton-on-Sea"
        elif addr_str.endswith(", Dovercourt") or addr_str.endswith(", Ramsey") or addr_str.endswith(", Parkeston"):
            addr_str += ", Harwich"
        elif addr_str.endswith(", Kirby Cross") or addr_str.endswith(", Kirby Le Soken"):
            addr_str += ", Frinton-on-Sea"
        elif addr_str.endswith(", Wix"):
            addr_str += ", Manningtree"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
