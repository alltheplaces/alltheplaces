import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbGlasgowSpider(OwenBaseSpider):
    name = "gb_glasgow"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # Glasgow City Council, address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1M9eQSuztYcHNtdF3xtynCn_WoMFiMsnH"
    csv_filename = "GLASGOW_CTBANDS_OSOU_202602.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"(.+?), (BAILLIESTON|BRIDGETON|CARMUNNOCK|CARMYLE|CLARKSTON|GARROWHILL BAILLIESTON|MOUNT VERNON|SPRINGBOIG|UDDINGSTON)$"
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        item["street_address"] = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]])
            .removesuffix(" GLASGOW")
            .strip(" ,")
        )
        if m := self._re.match(item["street_address"]):
            item["street_address"], item["extras"]["addr:suburb"] = m.groups()

        item["city"] = "Glasgow"
        item["country"] = "GB"
