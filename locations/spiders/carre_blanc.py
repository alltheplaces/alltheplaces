from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CarreBlancSpider(CrawlSpider, StructuredDataSpider):
    name = "carre_blanc"
    item_attributes = {"brand": "Carré blanc", "brand_wikidata": "Q55596025"}
    start_urls = ["http://boutiques.carreblanc.com/"]
    rules = [
        # Example: https://boutiques.carreblanc.com/linge-de-maison/montlucon/MON
        Rule(LinkExtractor(allow=r"https://boutiques.carreblanc.com/[\w-]+/[\w-]+/[\w\w\w]"), callback="parse_sd"),
        Rule(
            LinkExtractor(
                allow=r"https://boutiques.carreblanc.com/[\w-]+",
                restrict_xpaths='//div[contains(@class,"coutry-list")]/p/a',
            ),
            follow=True,
        ),
    ]
