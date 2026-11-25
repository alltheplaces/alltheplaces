import re
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_20
# https://www.owenboswarva.com/blog/post-addr109.htm


class GbEastHertfordshireSpider(UprnEnhancerSpider):
    name = "gb_east_hertfordshire"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_20/response/3499789/attach/2/PropertieswithBandsEHC%201.csv?cookie_passthrough=1"
    ]

    ref_column = "property_ref"
    uprn_column = "uprn"
    address_columns = ["addr"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?[,|\s] (?P<city>{})$".format(
                "|".join(
                    [
                        "BRAUGHING",
                        "DATCHWORTH",
                        "GREAT AMWELL",
                        "HERTFORD HEATH",
                        "HUNSDON",
                        "LITTLE HADHAM",
                        "PUCKERIDGE",
                        "ST MICHAELS MEAD",
                        "STANDON",
                        "STANSTEAD ABBOTTS",
                        "TEWIN",
                        "WALKERN",
                        "WATTON AT STONE",
                    ]
                ),
                "|".join(
                    [
                        "BISHOP'S STORTFORD",
                        "BUNTINGFORD",
                        "HARLOW",
                        "HERTFORD",
                        "KNEBWORTH",
                        "MUCH HADHAM",
                        "SAWBRIDGEWORTH",
                        "STEVENAGE",
                        "WARE",
                        "WELWYN",
                    ]
                ),
            )
        )

    def pre_process_data(self, addr: dict, **kwargs) -> None:
        addr["addr"] = (
            merge_address_lines([addr["addr1"], addr["addr2"], addr["addr3"], addr["addr4"]])
            .removesuffix(" HERTS")
            .removesuffix(" HERTFORDSHIRE")
            .removesuffix(" ESSEX")
            .replace(", WATTON-AT-STONE", ", WATTON AT STONE")
            .replace(", BISHOPS STORTFORD", ", BISHOP'S STORTFORD")
            .strip(" ,")
        )

    def post_process_item(self, item: Feature, response: Response, addr: dict, **kwargs) -> Iterable[Feature]:
        if (
            not addr["addr1"]
            or "SET UP IN ERROR" in addr["addr"]
            or "******" in addr["addr"]
            or "DUMMY" in addr["addr"]
        ):
            return
        yield item
