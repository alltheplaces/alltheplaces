from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class JaloucityDESpider(CrawlSpider):
    name = "jaloucity_de"
    item_attributes = {"brand": "JalouCity", "brand_wikidata": "Q113686657"}
    allowed_domains = ["www.jaloucity.de"]
    start_urls = ["https://www.jaloucity.de/filialen.html"]
    rules = [Rule(LinkExtractor(allow=r"/filialen/[\w-]+\.html$"), callback="parse_store", follow=False)]

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        if item := LinkedDataParser.parse(response, "LocalBusiness"):
            item["ref"] = response.url
            apply_category(Categories.SHOP_WINDOW_BLIND, item)
            yield item
