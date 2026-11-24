from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_12
# https://www.owenboswarva.com/blog/post-addr101.htm


class GbStratfordOnAvonSpider(UprnEnhancerSpider):
    name = "gb_stratford_on_avon"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_12/response/3447054/attach/2/attachment.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Place_Ref"
    uprn_column = "UPRN"
    address_columns = ["PropAddress_1", "PropAddress_2", "PropAddress_4", "PropAddress_5"]
