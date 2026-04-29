import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbArunSpider(OwenBaseSpider):
    name = "gb_arun"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1030scDO9gFByATcXGQK5Ao7m9pTYW5Xs"
    csv_filename = "ARUN_CTBANDS_OSOU_202602.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?(?:, ({}))?(?:,? West Sussex)?$".format(
                "|".join(
                    [
                        # "suburbs"
                        "Pagham",
                        "Bersted",
                        "Rustington",
                        "East Preston",
                        "Angmering",
                        "Wick",
                        "Yapton",
                        "Middleton-On-Sea",
                        "Barnham",
                        "Felpham",
                        "Eastergate",
                        "Findon",
                        "Walberton",
                        "Westergate",
                        "Fontwell",
                        "Ferring",
                        "Climping",
                        "Aldingbourne",
                        "Tortington",
                        "Middleton On Sea",
                        "Clapham",
                        "Slindon",
                        "Slindon Common",
                        "Patching",
                        "Poling",
                        "Burpham",
                        "Ford",
                        "Aldwick",
                        "Woodgate",
                    ]
                ),
                "|".join(
                    [
                        # cities
                        "Arundel",
                        "Barnham",
                        "Bognor Regis",
                        "Chichester",
                        "Littlehampton",
                        "Nr Bognor Regis",
                        "Worthing",
                        "Madehurst",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        if m := self._re.match(addr["ADDR"]):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])
