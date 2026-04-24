import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbMertonSpider(OwenBaseSpider):
    name = "gb_merton"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1IVA40BoURj5e5LKLMxMxRcBieFntrWKi"
    csv_filename = "MERTON_CTBANDS_OSOU_202602.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"(.+?), (?:(Wimbledon|Sutton|Colliers Wood|Raynes Park), )?(London|Mitcham|Morden|New Malden)$"
        )

        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines(
                [
                    addr["ADDR1"],
                    addr["ADDR2"],
                    addr["ADDR3"],
                    addr["ADDR4"],
                    addr["ADDR5"],
                ]
            )
            .replace(", Surrrey", ", Surrey")
            .replace(", Surey", ", Surrey")
            .replace(", Suurey", ", Surrey")
            .replace(", Mitcham, Surrey", ", Mitcham")
            .replace(", SUTTON", ", Sutton")
            .replace(", T20don", ", London")
            .replace(", Carshalton Road  Mitcham", ", Carshalton Road, Mitcham")
            .replace("Garth Road, Moren", "Garth Road, Morden")
            .replace("Church Road, Merton", "Church Road, Colliers Wood, London")
        )

        if (
            addr_str.endswith(", Wimbledon")
            or addr_str.endswith(", Sutton")
            or addr_str.endswith(", Thornton Heath")
            or addr_str.endswith(", Raynes Park")
        ):
            addr_str += ", London"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
