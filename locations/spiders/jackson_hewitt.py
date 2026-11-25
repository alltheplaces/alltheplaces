from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JacksonHewittSpider(SitemapSpider, StructuredDataSpider):
    name = "jackson_hewitt"
    item_attributes = {"brand": "Jackson Hewitt", "brand_wikidata": "Q6117132"}
    allowed_domains = ["jacksonhewitt.com"]
    sitemap_urls = ["https://office.jacksonhewitt.com/sitemap.xml"]
    sitemap_rules = [
        (r"/\d+$", "parse"),
    ]
    drop_attributes = {"image"}
    wanted_types = ["AccountingService"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if response.css(".Core-walmart"):
            item["located_in"] = "Walmart"
            item["located_in_wikidata"] = "Q483551"
        apply_category(Categories.OFFICE_TAX_ADVISOR, item)
        yield item
