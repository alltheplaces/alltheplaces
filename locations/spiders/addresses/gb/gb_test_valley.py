from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_7
# https://www.owenboswarva.com/blog/post-addr96.htm


class GbTestValleySpider(UprnEnhancerSpider):
    name = "gb_test_valley"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_7/response/3442035/attach/3/FOI%2010885.csv?cookie_passthrough=1"
    ]

    ref_column = "Property Reference Number"
    uprn_column = "Property UPRN"
    address_columns = ["Full Property Address"]
