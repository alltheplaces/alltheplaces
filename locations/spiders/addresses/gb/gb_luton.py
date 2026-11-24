from collections.abc import Iterator

from scrapy.http import Response

from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_2
# https://www.owenboswarva.com/blog/post-addr90.htm


class GbLutonSpider(UprnEnhancerSpider):
    name = "gb_luton"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_2/response/3450319/attach/3/FOI%20LU29084.xlsx?cookie_passthrough=1"
    ]

    ref_column = "Property reference"
    uprn_column = "UPRN"
    address_columns = ["address line 1", "address Line 2 ", "address line 3 "]
