from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SoulcycleSpider(CrawlSpider, StructuredDataSpider):
    name = "soulcycle"
    item_attributes = {"brand": "Soulcycle", "brand_wikidata": "Q17084730"}
    start_urls = ("https://www.soul-cycle.com/studios/all/",)
    rules = [
        Rule(LinkExtractor(allow="/studios/"), callback="parse_sd"),
    ]
    search_for_amenity_features = False
