from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CaliforniaClosetsSpider(CrawlSpider, StructuredDataSpider):
    name = "california_closets"
    item_attributes = {
        "brand_wikidata": "Q5020325",
        "brand": "California Closets",
    }
    start_urls = ["https://www.californiaclosets.com/showrooms/"]
    wanted_types = ["LocalBusiness", "HomeGoodsStore"]
    rules = [
        Rule(
            LinkExtractor(restrict_xpaths='//a[contains(text(), "Showroom details")]'),
            callback="parse_sd",
        )
    ]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("California Closets - ")
        yield item
