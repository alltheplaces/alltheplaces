import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider

class FonehouseGBSpider(CrawlSpider, StructuredDataSpider):
    name = "fonehouse_gb"
    item_attributes = {
        "brand": "fonehouse",
        "brand_wikidata": "Q130535827",
        "country": "GB",
    }

    start_urls = ["https://www.fonehouse.co.uk/store-finder"]
    rules = [Rule(LinkExtractor(allow=r"/stores/([^/]+)$"), callback="parse_sd")]
    wanted_types = ["LocalBusiness"]

