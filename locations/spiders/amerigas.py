from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AmerigasSpider(SitemapSpider, StructuredDataSpider):
    name = "amerigas"
    item_attributes = {"brand": "AmeriGas", "brand_wikidata": "Q23130318"}

    # Note, /api/search is forbidden by robots.txt, this spider produces their
    # first-party retail locations only, not third party tank exchange or refill

    sitemap_urls = ["https://www.amerigas.com/local_office_sitemap.xml.gz"]
    sitemap_rules = [
        (r"/locations/propane-offices/[^/]+/[^/]+/[^/]+$", "parse_sd"),
    ]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["openingHoursSpecification"] = None

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.VENDING_MACHINE, item)
        yield item
