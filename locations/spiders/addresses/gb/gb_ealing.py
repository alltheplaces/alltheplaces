import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbEalingSpider(OwenBaseSpider):
    name = "gb_ealing"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1WyMUpUoCCajp7PM20zoxpp6lkPotIGeQ"
    csv_filename = "EALING_CTBANDS_ONSUD_202511.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(, (Acton|Chiswick|Ealing|Hanwell|Park Royal|Perivale|West Ealing))?(, (Brentford|Greenford|London|Northolt|Southal|Southall|Wembley))?(, Middlesex|, Middx)?$"
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        if m := self._re.match(addr["ADDR"]):
            item["street_address"] = m.group(1)
            if m.group(3):
                item["extras"]["addr:suburb"] = m.group(3).lstrip(", ")
            if m.group(5):
                item["city"] = m.group(5).lstrip(", ")
                if item["city"] == "Southal":
                    item["city"] = "Southall"
        else:
            item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])

        item["extras"]["addr:county"] = "Middlesex"
