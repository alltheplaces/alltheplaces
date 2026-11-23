import re

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_11
# https://www.owenboswarva.com/blog/post-addr100.htm


class GbChichesterSpider(UprnEnhancerSpider):
    name = "gb_chichester"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_11/response/3455244/attach/4/Official.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Property Reference Number"
    uprn_column = "Property UPRN"
    address_columns = ["Full Property Address"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?(?:, (?P<city>{}))?,\s*(?:\s*\w\w?\d\d?\w?\s*[O\d]\w\w)?$".format(
                "|".join(
                    [
                        "Bosham",
                        "Bracklesham Bay",
                        "Easebourne",
                        "East Wittering",
                        "Fernhurst",
                        "Fishbourne",
                        "Selsey",
                        "Southbourne",
                        "Tangmere",
                        "West Wittering",
                        "Westbourne",
                    ]
                ),
                "|".join(
                    [
                        "Arundel",
                        "Billingshurst",
                        "Chichester",
                        "Cranleigh",
                        "Emsworth",
                        "Hambledon",
                        "Haslemere",
                        "Havant",
                        "Liphook",
                        "Liss",
                        "Midhurst",
                        "Petersfield",
                        "Petworth",
                        "Pulborough",
                    ]
                ),
            )
        )
