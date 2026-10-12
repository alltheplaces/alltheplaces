from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class HarvesterGBSpider(CrawlSpider, StructuredDataSpider):
    name = "harvester_gb"
    item_attributes = {"brand": "Harvester", "brand_wikidata": "Q5676915"}
    start_urls = ["https://www.harvester.co.uk/restaurants/"]
    rules = [Rule(LinkExtractor(allow="/restaurants/"), callback="parse_sd")]
