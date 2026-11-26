from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_5
# https://www.owenboswarva.com/blog/post-addr94.htm


class GbWarwickSpider(UprnEnhancerSpider):
    name = "gb_warwick"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_5/response/3433833/attach/2/attachment.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Place Ref"
    uprn_column = "UPRN"
    address_columns = [
        "PropAddress 1",
        "PropAddress 2",
        "PropAddress 3",
        "PropAddress 4",
        "PropAddress 5",
    ]

    def pre_process_data(self, addr: dict, **kwargs) -> None:
        for col in self.address_columns:
            if isinstance(addr.get(col), int):
                addr[col] = str(addr[col])
