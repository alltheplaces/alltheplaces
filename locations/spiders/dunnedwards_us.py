from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class DunnedwardsUSSpider(CrawlSpider, StructuredDataSpider):
    name = "dunnedwards_us"
    item_attributes = {"brand": "Dunn-Edwards Paints", "brand_wikidata": "Q110586577"}
    start_urls = ["https://www.dunnedwards.com/full-store-list/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.dunnedwards.com/paint-store/.*$"),
            callback="parse_sd",
        ),
    ]
