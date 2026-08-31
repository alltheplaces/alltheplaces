from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DeHypothekerNLSpider(SitemapSpider, StructuredDataSpider):
    name = "de_hypotheker_nl"
    item_attributes = {"brand": "De Hypotheker", "brand_wikidata": "Q2210766"}
    sitemap_urls = ["https://www.hypotheker.nl/sitemap/en-us/offices.xml"]
    sitemap_rules = [(r"\/branches\/[a-z0-9-]+\/[a-z0-9-]+\/$", "parse_sd")]
    wanted_types = ["FinancialService"]
    time_format = "%I:%M %p"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if not ld_data.get("geo"):
            return  # Duplicate ld
        item["name"] = None
        apply_category(Categories.OFFICE_FINANCIAL_ADVISOR, item)
        yield item
