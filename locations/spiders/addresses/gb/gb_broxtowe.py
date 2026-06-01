import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GBBroxtoweSpider(OwenBaseSpider):
    name = "gb_broxtowe"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "14Jal2XB6GV8HDsO4lQjNiiI910bYA4Gd"
    csv_filename = "BROXTOWE_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?(?:,? (?:{})?)?$".format(
                "|".join(
                    [
                        "Beeston",
                        "Stapleford",
                        "Eastwood",
                        "Nuthall",
                        "Kimberley",
                        "Bramcote",
                        "Chilwell",
                        "Newthorpe",
                        "Giltbrook",
                        "Brinsley",
                        "Awsworth",
                        "Trowell",
                        "Watnall",
                        "Toton",
                        "Attenborough",
                        "Cossall",
                    ]
                ),
                "|".join(
                    [
                        "Nottingham",
                        "Nottinghamshire",
                        "Notingham",
                        "Nottm",
                        "Notttingham",
                        "Nottinham",
                        "Notitngham",
                        "Nottngham",
                        "Nottinghan",
                        "Notiingham",
                        "Notts",
                        "Nottintgham",
                        "Nottinngham",
                        "Nottinmgham",
                        "Nottinghm",
                        "Nottimgham",
                        "Notrtingham",
                        "Nottinhgam",
                        "Noittingham",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"], addr["ADDR5"]])
            .replace(", Chilwell Beestonnottingham", ", Chilwell Beeston, Nottingham")
            .replace(", Chilwellbeeston", ", Chilwell Beeston")
        )
        item["city"] = "Nottingham"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
