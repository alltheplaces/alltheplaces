import re

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_13
# https://www.owenboswarva.com/blog/post-addr103.htm


class GbKnowsleySpider(UprnEnhancerSpider):
    name = "gb_knowsley"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_13/response/3477115/attach/3/KNW%20Domestic%20Properties.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Property Reference Number"
    uprn_column = "Property UPRN"
    address_columns = ["Full Property Address"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?(?:, (?P<city>{}))?(?:, (?:Merseyside|Cheshire)?)?(?:,\s*\w\w?\d\d?\w? \d\w\w)?$".format(
                "|".join(
                    [
                        "Cronton",
                        "Fazakerley",
                        "Halewood",
                        "Huyton",
                        "Kirkby",
                        "Knowsley Village",
                        "Melling",
                        "Roby",
                        "Simonswood",
                        "Stockbridge Village",
                        "Tarbock",
                        "Whiston",
                    ]
                ),
                "|".join(
                    [
                        "Knowsley",
                        "Liverpool",
                        "Prescot",
                        "St Helens",
                        "Widnes",
                    ]
                ),
            )
        )
