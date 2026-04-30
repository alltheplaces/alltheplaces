import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbCalderdaleSpider(OwenBaseSpider):
    name = "gb_calderdale"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "16KtuVd7YYUau7K8aQMbbqA3G-Y2C0SZ0"
    csv_filename = "CALDERDALE_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "Rishworth",
                        "Barkisland",
                        "Luddendenfoot",
                        "Greetland",
                        "Stainland",
                        "Shelf",
                        "Holywell Green",
                        "Northowram",
                        "Mytholmroyd",
                        "Southowram",
                        "Siddal",
                        "Bailiff Bridge",
                        "Illingworth",
                        "Ovenden",
                        "Mixenden",
                        "Rastrick",
                        "Ripponden",
                        "Hipperholme",
                        "Pellon",
                        "Lightcliffe",
                    ]
                ),
                "|".join(
                    [
                        "Bradford",
                        "Brighouse",
                        "Cleckheaton",
                        "Elland",
                        "Halifax",
                        "Hebden Bridge",
                        "Huddersfield",
                        "Mirfield",
                        "Sowerby Bridge",
                        "Todmorden",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]])
        if addr_str.endswith(", Rishworth"):
            addr_str += ", Sowerby Bridge"
        elif (
            addr_str.endswith(", Barkisland")
            or addr_str.endswith(", Luddendenfoot")
            or addr_str.endswith(", Greetland")
            or addr_str.endswith(", Stainland")
            or addr_str.endswith(", Shelf")
            or addr_str.endswith(", Holywell Green")
            or addr_str.endswith(", Northowram")
        ):
            addr_str += ", Halifax"
        elif addr_str.endswith(", Mytholmroyd"):
            addr_str += ", Hebden Bridge"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
