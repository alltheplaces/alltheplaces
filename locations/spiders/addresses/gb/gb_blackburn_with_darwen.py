import re

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_3
# https://www.owenboswarva.com/blog/post-addr92.htm


class GbBlackburnWithDarwenSpider(UprnEnhancerSpider):
    name = "gb_blackburn_with_darwen"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_3/response/3430059/attach/2/Live%20props%20with%20Prop%20Ref%20UPRN%20and%20Current%20Band.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Property Reference Number"
    uprn_column = "Property UPRN"
    address_columns = ["Full Property Address"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?, (?P<city>{})\.?(?:, (?:Lancs|Lancashire))?(?:,\s*\w\w?\d\d?\w?\s*[\dO]\w\w)$".format(
                "|".join(
                    [
                        "Belmont",
                        "Chapeltown",
                        "Cherry Tree",
                        "Edgworth",
                        "Feniscowles",
                        "Fernhurst Farm",
                        "Hoddlesden",
                        "Livesey",
                        "Lower Darwen",
                        "Oakdale",
                        "Pleasington",
                    ]
                ),
                "|".join(
                    [
                        "Blackburn",
                        "Bolton",
                        "Bury",
                        "Chorley",
                        "Darwen",
                        "Turton",
                    ]
                ),
            )
        )

    def pre_process_data(self, addr: dict, **kwargs) -> None:
        addr["Full Property Address"] = addr["Full Property Address"].replace(
            ", Blackburn, Larmenier Care Village , ", ", Larmenier Care Village, Blackburn, "
        )
