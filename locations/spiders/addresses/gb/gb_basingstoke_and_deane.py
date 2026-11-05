from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_19
# https://www.owenboswarva.com/blog/post-addr108.htm


class GbBasingstokeAndDeaneSpider(UprnEnhancerSpider):
    name = "gb_basingstoke_and_deane"
    onsud_region = "SE"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_19/response/3465756/attach/2/1158907%20Copy%20of%20FOI%201253.25%20002.xlsx?cookie_passthrough=1"
    ]

    ref_column = "PRN:"
    uprn_column = "UPRN:"
    address_columns = ["Address:"]
