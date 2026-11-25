import re

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_24
# https://www.owenboswarva.com/blog/post-addr114.htm


class GbChorleySpider(UprnEnhancerSpider):
    name = "gb_chorley"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_24/response/3512914/attach/7/CBC%2026%20354%20data%20for%20response.xlsx?cookie_passthrough=1"
    ]

    ref_column = "property_ref"
    uprn_column = "uprn"
    address_columns = ["addr1", "addr2", "addr3"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?(?:, (?P<city>{}))?$".format(
                "|".join(
                    [
                        "ADLINGTON",
                        "ANDERTON",
                        "ASTLEY VILLAGE",
                        "BAMBER BRIDGE",
                        "BRINSCALL",
                        "BUCKSHAW VILLAGE",
                        "CHARNOCK RICHARD",
                        "CLAYTON-LE-WOODS",
                        "COPPULL",
                        "CROSTON",
                        "ECCLESTON",
                        "EUXTON",
                        "FENISCOWLES",
                        "HEATH CHARNOCK",
                        "HESKIN",
                        "MAWDESLEY",
                        "WHITTLE-LE-WOODS",
                        "WITHNELL",
                        "WRIGHTINGTON",
                    ]
                ),
                "|".join(
                    [
                        "CHORLEY",
                        "LEYLAND",
                        "ORMSKIRK",
                        "PRESTON",
                    ]
                ),
            )
        )
