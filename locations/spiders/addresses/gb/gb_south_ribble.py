import re
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_28
# https://www.owenboswarva.com/blog/post-addr117.htm


class GbSouthRibbleSpider(UprnEnhancerSpider):
    name = "gb_south_ribble"
    onsud_region = "NW"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_28/response/3515941/attach/6/SRBC269801.xlsx?cookie_passthrough=1"
    ]

    ref_column = "property_ref1"
    uprn_column = "uprn"
    address_columns = ["addr1", "addr2", "addr3"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?, (?P<city>{})$".format(
                "|".join(
                    [
                        "BAMBER BRIDGE",
                        "BUCKSHAW VILLAGE",
                        "FARINGTON",
                        "LONGTON",
                        "LOSTOCK HALL",
                        "MOSS SIDE",
                        "NEW LONGTON",
                        "PENWORTHAM",
                        "WALTON-LE-DALE",
                    ]
                ),
                "|".join(["BLACKBURN", "CHORLEY", "LEYLAND", "PRESTON"]),
            )
        )

    def post_process_item(self, item: Feature, response: Response, addr: dict, **kwargs) -> Iterable[Feature]:
        if "DUFF" in addr["addr1"] or "NOT TO BE USED" in addr["addr1"]:
            return None
        if city := item.get("city"):
            item["city"] = city.title()
        yield item
