from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


# Sitemap is currently out of date
class OshkoshUSSpider(CrawlSpider, StructuredDataSpider):
    name = "oshkosh_us"
    item_attributes = {"brand": "OshKosh B'gosh", "brand_wikidata": "Q1417347"}
    start_urls = ["https://locations.oshkosh.com/"]
    rules = [
        Rule(LinkExtractor(r"\.com/\w\w/$")),
        Rule(LinkExtractor(r"\.com/\w\w/[^/]+/$")),
        Rule(LinkExtractor(r"\.com/\w\w/[^/]+/[^/]+$"), "parse"),
    ]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False
