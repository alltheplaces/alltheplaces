import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbSouthNorfolkSpider(OwenBaseSpider):
    name = "gb_south_norfolk"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1o5hy7exhkxVSGXgWDNNDwPabum0vxQA5"
    csv_filename = "SOUTHNORFOLK_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "Brooke",
                        "Chedgrave",
                        "Costessey",
                        "Cringleford",
                        "Dickleburgh",
                        "Ditchingham",
                        "Framingham Earl",
                        "Hales",
                        "Heckingham",
                        "Hempnall",
                        "Hethersett",
                        "Hingham",
                        "Little Melton",
                        "Loddon",
                        "Long Stratton",
                        "Mulbarton",
                        "Newton Flotman",
                        "Poringland",
                        "Pulham Market",
                        "Roydon",
                        "Scole",
                        "Stoke Holy Cross",
                        "Topcroft",
                        "Trowse",
                    ]
                ),
                "|".join(
                    ["Beccles", "Bungay", "Dereham", "Diss", "Great Yarmouth", "Harleston", "Norwich", "Wymondham"]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = merge_address_lines([addr["ADDR"].removesuffix("Norfolk").removesuffix("Suffolk").strip(", ")])
        if (
            addr_str.endswith(", Costessey")
            or addr_str.endswith(", Poringland")
            or addr_str.endswith(", Trowse")
            or addr_str.endswith(", Loddon")
            or addr_str.endswith(", Little Melton")
            or addr_str.endswith(", Hempnall")
            or addr_str.endswith(", Heckingham")
            or addr_str.endswith(", Hales")
        ):
            addr_str += ", Norwich"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
