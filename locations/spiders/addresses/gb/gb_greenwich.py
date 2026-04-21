import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbGreenwichSpider(OwenBaseSpider):
    name = "gb_greenwich"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1bErEyfJ4C4rEP1XnDIVkM7Hby50NP1n0"
    csv_filename = "GREENWICH_CTBANDS_ONSUD_202512.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(, ({}))?(, ({}))?(, KENT)?$".format(
                "|".join(  # "suburbs"
                    [
                        "ABBEY WOOD",
                        "BLACKHEATH",
                        "CHARLTON",
                        "CHERRY ORCHARD ESTATE",
                        "DEPTFORD",
                        "ELTHAM",
                        "GREENWICH",
                        "KIDBROOKE",
                        "LEE",
                        "LEWISHAM",
                        "MOTTINGHAM",
                        "NEW ELTHAM",
                        "PLUMSTEAD",
                        "SHOOTERS HILL",
                        "THAMESMEAD",
                        "WOOLWICH",
                    ]
                ),
                "|".join(  # "cities"
                    [
                        "CHISLEHURST",
                        "LONDON",
                        "SIDCUP",
                        "WELLING",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        item["ref"] = addr["ORDID"]
        item["addr_full"] = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]])
            .replace(", LONDOIN", ", LONDON")
            .replace(", LONON", ", LONDON")
            .replace(", LOMNDON", ", LONDON")
            .replace("ASHBURNHAM PLACE GREENWICH", "ASHBURNHAM PLACE, GREENWICH")
        )
        if m := self._re.match(item["addr_full"]):
            item["street_address"] = m.group(1)
            if m.group(3):
                item["extras"]["addr:suburb"] = m.group(3).title()

            if m.group(5):
                item["city"] = m.group(5).title()

            if m.group(6):
                item["extras"]["addr:county"] = "Kent"
        else:
            item["addr_full"] = merge_address_lines([item["addr_full"], item.get("postcode")])
