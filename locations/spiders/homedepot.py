from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class HomeDepotSpider(CrawlSpider, StructuredDataSpider):
    name = "homedepot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["www.homedepot.com"]
    start_urls = [
        "https://www.homedepot.com/l/storeDirectory",
    ]
    rules = [
        Rule(LinkExtractor(allow=r"^https:\/\/www.homedepot.com\/l\/..$")),
        Rule(LinkExtractor(allow=r"^https:\/\/www.homedepot.com\/l\/.*\/\d*$"), callback="parse_sd"),
    ]
    requires_proxy = "US"
