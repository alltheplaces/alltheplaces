from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


# Can't currently use StructuredDataSpider as there is no type in the source data
class AtiPhysicalTherapySpider(SitemapSpider, StructuredDataSpider):
    name = "ati_physical_therapy"
    item_attributes = {
        "brand": "ATI Physical Therapy",
        "brand_wikidata": "Q50039703",
        "country": "US",
    }
    allowed_domains = ["locations.atipt.com"]
    sitemap_urls = ["https://locations.atipt.com/sitemap.xml"]
    sitemap_rules = [(r"\.com\/[^/]+/[^/]+/\d+-[a-z-]+/$", "parse_sd")]
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
