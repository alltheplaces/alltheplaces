import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GBEastRidingOfYorkshireSpider(OwenBaseSpider):
    name = "gb_east_riding_of_yorkshire"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1IyMpkJE5BE79x779QwHaD6sgoIoMnRpp"
    csv_filename = "ERY_CTBANDS_OSOI_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?(?:, ({}))?(?:, East Riding of Yorkshire)?$".format(
                "|".join(
                    [
                        "Aldbrough",
                        "Anlaby",
                        "Anlaby Common",
                        "Barmby Moor",
                        "Beeford",
                        "Bilton",
                        "Brandesburton",
                        "Burstwick",
                        "Cherry Burton",
                        "Elloughton",
                        "Flamborough",
                        "Gilberdyke",
                        "Hedon",
                        "Holme On Spalding Moor",
                        "Hook",
                        "Howden",
                        "Keyingham",
                        "Kilham",
                        "Kirkella",
                        "Leconfield",
                        "Leven",
                        "Market Weighton",
                        "Molescroft",
                        "Nafferton",
                        "Newport",
                        "North Cave",
                        "Patrington",
                        "Pocklington",
                        "Preston",
                        "Rawcliffe",
                        "Skidby",
                        "Skirlaugh",
                        "Snaith",
                        "South Cave",
                        "Sproatley",
                        "Stamford Bridge",
                        "Swanland",
                        "Thorngumbald",
                        "Tickton",
                        "Walkington",
                        "Welton",
                        "Wilberfoss",
                        "Willerby",
                        "Woodmansey",
                    ]
                ),
                "|".join(
                    [
                        "Beverley",
                        "Bridlington",
                        "Brough",
                        "Cottingham",
                        "Driffield",
                        "Goole",
                        "Hessle",
                        "Hornsea",
                        "Hull",
                        "North Ferriby",
                        "Withernsea",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            addr["ADDR"]
            .replace(", East Riding Yorkshire", ", East Riding of Yorkshire")
            .replace(", East Rdiing Of Yorkshire", ", East Riding of Yorkshire")
            .replace(", Kirk Ella", ", Kirkella")
        )

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
            if not (item["extras"]["addr:suburb"] or item["city"]):
                item["street_address"] = None
                item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
