from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class KorianFRSpider(CrawlSpider, StructuredDataSpider):
    name = "korian_fr"
    item_attributes = {"brand": "Korian", "brand_wikidata": "Q3198944"}
    start_urls = ["https://www.korian.fr/maisons-retraite"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.korian.fr/maisons-retraite/[-\w]+/[-\w]+/[-\w]+/[-\w]+$"),
            callback="parse_sd",
        )
    ]
