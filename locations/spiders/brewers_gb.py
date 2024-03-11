from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class BrewersGBSpider(CrawlSpider, StructuredDataSpider):
    name = "brewers_gb"
    item_attributes = {"brand": "Brewers", "brand_wikidata": "Q121435210"}
    start_urls = ["https://www.brewers.co.uk/stores"]
    download_delay = 3  # Requested by robots.txt
    rules = [Rule(LinkExtractor(r"/stores/[^/]+/(\w\w\w)"), callback="parse")]
    wanted_types = ["Store"]
