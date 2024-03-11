from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class LinvosgesFRSpider(CrawlSpider, StructuredDataSpider):
    name = "linvosges_fr"
    item_attributes = {"brand": "Linvosges", "brand_wikidata": "Q94359140"}
    start_urls = ["https://www.linvosges.com/fr/nos-magasins/"]
    rules = [
        Rule(LinkExtractor(allow=r"fr/nos-magasins/[\w-]+"), callback="parse_sd"),
    ]
