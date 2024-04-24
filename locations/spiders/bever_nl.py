from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class BeverNLSpider(CrawlSpider, StructuredDataSpider):
    name = "bever_nl"
    item_attributes = {"brand": "Bever", "brand_wikidata": "Q123596881"}
    start_urls = ["https://www.bever.nl/winkels.html"]
    rules = [
        Rule(LinkExtractor(allow="/winkels/", restrict_xpaths='//a[@class="alphabetical-list__link"]'), "parse_sd")
    ]
