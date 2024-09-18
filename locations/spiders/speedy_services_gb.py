from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SpeedyServicesGBSpider(CrawlSpider, StructuredDataSpider):
    name = "speedy_services_gb"
    item_attributes = {
        "brand": "Speedy",
        "brand_wikidata": "Q7575722",
    }
    start_urls = ["https://www.speedyservices.com/depot/a-z"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.speedyservices.com/depot/[\w-]+-\d+"),
            callback="parse",
        ),
    ]
