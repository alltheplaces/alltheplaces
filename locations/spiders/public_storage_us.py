from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PublicStorageUSSpider(CrawlSpider, StructuredDataSpider):
    name = "public_storage_us"
    item_attributes = {"brand": "Public Storage", "brand_wikidata": "Q1156045"}
    allowed_domains = ["www.publicstorage.com"]
    start_urls = ["https://www.publicstorage.com/site-map-states"]
    rules = [
        Rule(LinkExtractor(allow=r"/site-map-states-[-\w]+$")),
        Rule(LinkExtractor(allow=r"/self-storage-.+/\d+.html$"), callback="parse_sd"),
    ]
    wanted_types = ["SelfStorage"]
