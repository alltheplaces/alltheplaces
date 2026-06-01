from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DozPLSpider(CrawlSpider, StructuredDataSpider):
    name = "doz_pl"
    item_attributes = {"brand": "Dbam o Zdrowie", "brand_wikidata": "Q62563833"}
    allowed_domains = ["www.doz.pl"]
    start_urls = ["https://www.doz.pl/apteki"]
    rules = [
        Rule(LinkExtractor(allow=r"/apteki/w\d+-")),
        Rule(LinkExtractor(allow=r"/apteki/m\d+-")),
        Rule(LinkExtractor(allow=r"/apteki/a\d+-"), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        apply_category(Categories.PHARMACY, item)
        del item["facebook"]  # privacy policy link
        yield item
