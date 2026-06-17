from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class EuropeanWaxCenterUSSpider(CrawlSpider, StructuredDataSpider):
    name = "european_wax_center_us"
    item_attributes = {
        "brand_wikidata": "Q5413426",
        "brand": "European Wax Center",
    }
    start_urls = ["https://locations.waxcenter.com/"]
    sitemap_rules = [(r"https://locations.waxcenter.com/[^/]+/[^/]+/[^/]+\.html$", "parse_sd")]
    rules = [
        Rule(LinkExtractor(allow=r"https://locations.waxcenter.com/\w+/$")),
        Rule(LinkExtractor(allow=r"https://locations.waxcenter.com/\w+/[a-z-]+/$")),
        Rule(LinkExtractor(allow=r"https://locations.waxcenter.com/\w+/[a-z-]+/[a-z-0-9\.]+$"), callback="parse_sd"),
    ]
