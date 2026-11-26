from collections.abc import Iterator
from itertools import islice

from scrapy.http import Response

from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_15
# https://www.owenboswarva.com/blog/post-addr105.htm


class GbSouthendOnSeaSpider(UprnEnhancerSpider):
    name = "gb_southend_on_sea"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_15/response/3465779/attach/8/UPRNs%20and%20Addresses.xlsx?cookie_passthrough=1"
    ]

    ref_column = "UPRN"
    uprn_column = "UPRN"
    address_columns = ["ADDRESS"]

    def iter_rows(self, response: Response) -> Iterator[tuple]:
        yield from islice(super().iter_rows(response), 1, None)

    def pre_process_data(self, addr: dict, **kwargs) -> None:
        addr["ADDRESS"] = merge_address_lines(addr["ADDRESS"].split("\n"))
