import re


from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_4
# https://www.owenboswarva.com/blog/post-addr93.htm


class GbHorshamSpider(UprnEnhancerSpider):
    name = "gb_horsham"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_4/response/3457382/attach/4/Horsham%20DC%20Full%20Council%20Tax%20Property%20List.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Property Reference"
    uprn_column = "UPRN              "
    address_columns = [
        "Address 1                          ",
        "Address 2                          ",
        "Address 3                       ",
        "Address 4                       ",
    ]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?,? (?P<city>{})(?:,? (?:SURREY|WEST SUSSEX|WSET SUSSEX|WST SUSSEX|WSX))?$".format(
                "|".join(
                    [
                        "AMBERLEY",
                        "ASHINGTON",
                        "BARNS GREEN",
                        "BROADBRIDGE HEATH",
                        "CODMORE HILL",
                        "COWFOLD",
                        "FAYGATE",
                        "IFIELD",
                        "MANNINGS HEATH",
                        "PARTRIDGE GREEN",
                        "RUDGWICK",
                        "SLINFOLD",
                        "SMALL DOLE",
                        "SOUTHWATER",
                        "STORRINGTON",
                        "THAKEHAM",
                        "UPPER BEEDING",
                        "WARNHAM",
                        "WASHINGTON",
                        "WEST CHILTINGTON",
                    ]
                ),
                "|".join(
                    [
                        "ARUNDEL",
                        "BILLINGSHURST",
                        "CRAWLEY",
                        "DORKING",
                        "HAYWARDS HEATH",
                        "HENFIELD",
                        "HORSHAM",
                        "PULBOROUGH",
                        "SOUTHWATER",
                        "STEYNING",
                        "SHOREHAM-BY-SEA",
                    ]
                ),
            )
        )
