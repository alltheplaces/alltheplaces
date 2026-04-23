import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbMansfieldSpider(OwenBaseSpider):
    name = "gb_mansfield"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2025."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1SptFBi7BtsVA_bTWbjWHzmnVZLkTD6QU"
    csv_filename = "MANSFIELD_CTBANDS_OSOU_202602.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"(.+?), (?:(Mansfield Woodhouse|Forest Town|Warsop|Church Warsop|Meden Vale|Rainworth|Warsop Vale), )?(Mansfield|Sookholme Warsop|Sutton-In-Ashfield), Nottinghamshire$"
        )

        return spider

    def parse_row(self, item: Feature, addr: dict):
        if m := self._re.match(
            addr["ADDR"]
            .replace(", Mansfield Nottinghamshire", ", Mansfield, Nottinghamshire")
            .replace(", Mansfield Woodhouse, Nottinghamshire", ", Mansfield Woodhouse, Mansfield, Nottinghamshire"),
        ):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])

        item["extras"]["addr:county"] = "Nottinghamshire"
