import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbEastSuffolkSpider(OwenBaseSpider):
    name = "gb_east_suffolk"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "11Qcv4eKHTzfRjXvxid9Ezl9y2-y0rkU4"
    csv_filename = "EASTSUFFOLK_CTBANDS_OSOU_202602.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"(.+), (ALDEBURGH|BECCLES|BUNGAY|FELIXSTOWE|HALESWORTH|HARLESTON|IPSWICH|LEISTON|LOWESTOFT|NORFOLK|SAXMUNDHAM|SOMERLEYTON|SOUTHWOLD|WOODBRIDGE)$"
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]])
            .removesuffix("SUFFOLK")
            .strip(" ,")
            .replace(", SAXMUNDAHM", ", SAXMUNDHAM")
        )
        if m := self._re.match(addr_str):
            item["street_address"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])

        item["extras"]["addr:county"] = "Suffolk"
