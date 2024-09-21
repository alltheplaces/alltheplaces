import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SbarroSpider(CrawlSpider, StructuredDataSpider):
    name = "sbarro"
    item_attributes = {"brand": "Sbarro", "brand_wikidata": "Q2589409"}
    allowed_domains = ["sbarro.com"]
    start_urls = ["https://sbarro.com/locations/?user_search=78749&radius=50000&count=5000"]
    rules = (
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="location-name "]'),
            follow=True,
            callback="parse_sd",
        ),
    )

    def post_process_item(self, item, response, ld_data):
       item["name"] = response.xpath('//*[@class="location-name "]/text()').extract_first()
       yield item

