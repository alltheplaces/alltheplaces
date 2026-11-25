import re

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_30
# https://www.owenboswarva.com/blog/post-addr119.htm


class GbHaltonSpider(UprnEnhancerSpider):
    name = "gb_halton"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_30/response/3540290/attach/3/Copy%20of%20FULL%20PROPERTY%20LIST%20FOI.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Property Reference Number"
    uprn_column = "Property UPRN"
    address_columns = [
        "Flat Number",
        "Building Number or Name",
        "Property Number",
        "All Sub Streets",
        "Street",
        "Area",
        "Town",
    ]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?(?:, (?P<city>{}))?(?:, (?:Cheshire|Merseyside))?$".format(
                "|".join(
                    [
                        "Hale",
                        "Norton",
                        "Farnworth",
                        "Daresbury",
                        "Moore",
                        "Preston Brook",
                    ]
                ),
                "|".join(
                    [
                        "Liverpool",
                        "Prescot",
                        "Runcorn",
                        "Warrington",
                        "Widnes",
                        "Nr Widnes",
                    ]
                ),
            )
        )
