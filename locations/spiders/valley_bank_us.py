from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ValleyBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "valley_bank_us"
    item_attributes = {"brand": "Valley Bank", "brand_wikidata": "Q7912152"}
    sitemap_urls = ["https://locations.valley.com/robots.txt"]
    sitemap_rules = [(r"/valley\-bank\-(\d+a?)\.html$", "parse")]
    wanted_types = ["BankorCreditUnion"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        item["facebook"] = None
        if response.url.endswith("a.html"):
            apply_category(Categories.ATM, item)
        else:
            item["branch"] = response.xpath('//a[@class="current--page"]/text()').get()
            apply_category(Categories.BANK, item)
        yield item
