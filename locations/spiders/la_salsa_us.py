from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class LaSalsaUSSpider(CrawlSpider, StructuredDataSpider):
    name = "la_salsa_us"
    item_attributes = {"brand": "La Salsa", "brand_wikidata": "Q48835190"}
    start_urls = ["https://www.lasalsa.com/locator/index.php?brand=26&pagesize=1000&q=us"]
    rules = [
        Rule(LinkExtractor(allow="/stores/"), callback="parse_sd"),
    ]
