from collections.abc import Iterator

from scrapy.http import Response

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_26
# https://www.owenboswarva.com/blog/post-addr115.htm


class GbWealdenSpider(UprnEnhancerSpider):
    name = "gb_wealden"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_26/response/3504968/attach/3/26%2027%20460%20Response%20Attachment.csv?cookie_passthrough=1"
    ]

    ref_column = "Property Reference  "
    uprn_column = "UPRN                "
    address_columns = [
        "Address 1                          ",
        "Address 2                          ",
        "Address 3                        ",
        "Address 4                        ",
    ]
