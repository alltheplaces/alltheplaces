from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class NicholsonsPubsGBSpider(CrawlSpider, StructuredDataSpider):
    name = "nicholsons_pubs_gb"
    item_attributes = {"brand": "Nicholson's", "brand_wikidata": "Q113130666"}
    start_urls = ["https://www.nicholsonspubs.co.uk/ourvenues"]
    rules = [Rule(LinkExtractor("/restaurants/"), "parse_sd")]
