from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class FrankieAndBennysGBSpider(CrawlSpider, StructuredDataSpider):
    name = "frankie_and_bennys_gb"
    item_attributes = {"brand": "Frankie & Benny's", "brand_wikidata": "Q5490892"}
    allowed_domains = ["www.frankieandbennys.com"]
    start_urls = ["https://www.frankieandbennys.com/restaurants/index.html"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/restaurants/[-\w]+/[-\w]+/[-\w]+$"),
            callback="parse_sd",
        ),
        Rule(LinkExtractor(allow=r"/restaurants/[-\w]+/?[-\w]+?$")),
    ]
    wanted_types = ["Restaurant"]
    search_for_email = False
    requires_proxy = True
