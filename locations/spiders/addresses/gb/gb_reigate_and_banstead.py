import re
from collections.abc import Iterator
from itertools import islice

from scrapy.http import Response

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_22
# https://www.owenboswarva.com/blog/post-addr112.htm


class GbReigateAndBansteadSpider(UprnEnhancerSpider):
    name = "gb_reigate_and_banstead"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_22/response/3479803/attach/2/attachment.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Property Reference Number"
    uprn_column = "Property UPRN"
    address_columns = ["Full Property Address"]

    def iter_rows(self, response: Response) -> Iterator[tuple]:
        yield from islice(super().iter_rows(response), 3, None)

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?, (?P<city>{})\s*(?:, Surrey,?)?(?:, \w\w?\d\d?\w?\s*\d\w\w)?$".format(
                "|".join(
                    [
                        "Belmont",
                        "Burgh Heath",
                        "Chipstead",
                        "Kingswood",
                        "Langshott",
                        "Lower Kingswood",
                        "Merstham",
                        "Netherne On The Hill",
                        "Salfords",
                        "Walton On The Hill",
                        "Woodmansterne",
                    ]
                ),
                "|".join(
                    [
                        "Banstead",
                        "Carshalton",
                        "Coulsdon",
                        "Epsom",
                        "Epsom Downs",
                        "Horley",
                        "Redhill",
                        "Reigate",
                        "Sutton",
                        "Tadworth",
                    ]
                ),
            )
        )
