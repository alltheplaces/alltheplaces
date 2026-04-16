import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GBStokeOnTrentSpider(OwenBaseSpider):
    name = "gb_stoke_on_trent"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings                                                                                # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1P9KpC-J3wZGAv48gpDnV3s_5VxllDVDX"
    csv_filename = "STOKE_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?: ({}))?, (Stoke-on-Trent|Newcastle Under Lyme)$".format(
                "|".join(
                    [
                        # "suburbs"
                        "Abbey Hulton",
                        "Adderley Green",
                        "Baddeley Edge",
                        "Baddeley Green",
                        "Ball Green",
                        "Basford",
                        "Bentilee",
                        "Berry Hill",
                        "Birches Head",
                        "Blurton",
                        "Bradeley",
                        "Bucknall",
                        "Burslem",
                        "Chell Heath",
                        "Chell",
                        "Cliff Vale",
                        "Cobridge",
                        "Dresden",
                        "Eaton Park",
                        "Etruria",
                        "Fegg Hayes",
                        "Fenton",
                        "Goldenhill",
                        "Hanford",
                        "Hanley",
                        "Hartshill",
                        "Heron Cross",
                        "Lightwood",
                        "Longport",
                        "Longton",
                        "Meir Hay",
                        "Meir Park",
                        "Meir",
                        "Middleport",
                        "Milton",
                        "Moss Green Village",
                        "Newstead",
                        "Normacot",
                        "Northwood",
                        "Norton Chase",
                        "Norton Green",
                        "Norton",
                        "Oakhill",
                        "Packmoor",
                        "Penkhull",
                        "Pittshill",
                        "Sandford Hill",
                        "Sandyford",
                        "Shelton",
                        "Smallthorne",
                        "Sneyd Green",
                        "Stanfield",
                        "Trent Vale",
                        "Trentham",
                        "Tunstall",
                        "Weston Coyney",
                    ]
                )
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        if (
            addr["ADDR"].endswith(", Burslem")
            or addr["ADDR"].endswith(", Stockton Brook")
            or addr["ADDR"].endswith(", Norton")
        ):
            addr["ADDR"] += ", Stoke-on-Trent"
        if m := self._re.match(
            addr["ADDR"]
            .replace(", Stoke-on-Trent, Baddeley Green", ", Baddeley Green, Stoke-on-Trent")
            .replace(", Stoke-on-Trent, Middleport", ", Middleport, Stoke-on-Trent")
            .replace(", Newcastle, Staffs", ", Newcastle Under Lyme")
        ):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])
