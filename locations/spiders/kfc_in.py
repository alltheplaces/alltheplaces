from typing import Iterable

from scrapy.http import Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class KfcINSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_in"
    item_attributes = KFC_SHARED_ATTRIBUTES
    sitemap_urls = ["https://restaurants.kfc.co.in/robots.txt"]
    sitemap_rules = [(r"/kfc-[-\w]+-(\d+)/Home", "parse_sd")]
    time_format = "%I:%M %p"

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if "openingHoursSpecification" in ld_obj.keys():  # desired ld_data
                yield ld_obj

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # city and state values are not correct, better to collect them to form addr_full
        item["addr_full"] = merge_address_lines(
            [item.pop("street_address"), item.pop("city"), item.pop("state"), item["postcode"]]
        )
        yield item
