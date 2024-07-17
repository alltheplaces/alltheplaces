from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class HarborFreightSpider(CrawlSpider, StructuredDataSpider):
    name = "harbor_freight"
    item_attributes = {"brand": "Harbor Freight Tools", "brand_wikidata": "Q5654601"}
    allowed_domains = ["harborfreight.com"]
    start_urls = ["https://www.harborfreight.com/storelocator/store-directory"]
    rules = [
        Rule(LinkExtractor(allow="/storelocator/store-directory/")),
        Rule(
            LinkExtractor(allow=r"\/storelocator\/.+-\d+\?number=\d+"),
            callback="parse_sd",
        ),
    ]
