import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class KindercareSpider(CrawlSpider, StructuredDataSpider):
    name = "kindercare"
    item_attributes = {
        "brand": "KinderCare Learning Centers",
        "brand_wikidata": "Q6410551",
    }
    allowed_domains = ["kindercare.com"]
    start_urls = [
        "https://www.kindercare.com/our-centers",
    ]
    download_delay = 0.5
    rules = [
        Rule(
            LinkExtractor(
                restrict_xpaths = ['//div[contains(@class, "link-index-results")]//li']
            ),
            callback="parse_sd",
            follow=True,
        )
    ]
