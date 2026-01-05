from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FuzzysTacoShopUSSpider(CrawlSpider, StructuredDataSpider):
    name = "fuzzys_taco_shop_us"
    item_attributes = {"brand": "Fuzzy's Taco Shop", "brand_wikidata": "Q85762348"}
    allowed_domains = ["fuzzystacoshop.com"]
    start_urls = ["https://fuzzystacoshop.com/locations/list/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/locations"),
            callback="parse_sd",
            follow=True,
        ),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Fuzzy's Taco Shop ").split(",")[0]
        yield item
