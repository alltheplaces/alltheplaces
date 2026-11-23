import re

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_8
# https://www.owenboswarva.com/blog/post-addr97.htm


class GbHerefordshireSpider(UprnEnhancerSpider):
    name = "gb_herefordshire"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_8/response/3438457/attach/2/Copy%20of%20ctax%20props.csv?cookie_passthrough=1"
    ]

    ref_column = "Property Ref"
    uprn_column = "Uprn"
    address_columns = ["Addr1", "Addr2", "Addr3", "Addr4"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?, (?P<city>{})(?:,? (?:HEREFORDSHIRE|WORCESTERSHIRE|SHROPSHIRE|HFDS|GLOS|POWYS|WORCS|GWENT))?$".format(
                "|".join(
                    [
                        "BARTESTREE",
                        "BELMONT",
                        "BODENHAM",
                        "BURGHILL",
                        "CLEHONGER",
                        "COLWALL",
                        "CRADLEY",
                        "CREDENHILL",
                        "HOLMER",
                        "KINGSTONE",
                        "LOWER BULLINGHAM",
                        "MADLEY",
                        "MARDEN",
                        "WEOBLEY",
                    ]
                ),
                "|".join(
                    [
                        "BROMYARD",
                        "CRAVEN ARMS",
                        "DRYBROOK",
                        "HEREFORD",
                        "KINGTON",
                        "KNIGHTON",
                        "LEDBURY",
                        "LEOMINSTER",
                        "LUDLOW",
                        "MALVERN",
                        "MONMOUTH",
                        "NEWENT",
                        "PRESTEIGNE",
                        "ROSS-ON-WYE",
                        "ROSS ON WYE",
                        "TENBURY WELLS",
                        "WORCESTER",
                    ]
                ),
            )
        )
