from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KorianFRSpider(CrawlSpider, StructuredDataSpider):
    name = "korian_fr"
    item_attributes = {"operator": "Korian", "operator_wikidata": "Q3198944"}
    start_urls = ["https://www.korian.fr/maisons-retraite"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.korian.fr/maisons-retraite/[-\w]+/[-\w]+/[-\w]+/[-\w]+$"),
            callback="parse_sd",
        )
    ]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SOCIAL_FACILITY, item)
        yield item
