from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from locations.structured_data_spider import StructuredDataSpider


class FordDealersUSSpider(CrawlSpider, StructuredDataSpider):
    name = "ford_dealers_us"
    item_attributes = {
        "brand": "Ford Motor Company",
        "brand_wikidata": "Q44294",
    }
    start_urls = ["https://www.ford.com/dealerships/dealer-directory/browse-all/"]
    wanted_types = ["AutoDealer"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https://www.ford.com/dealerships/dealer-directory/"),
        ),
        Rule(
            LinkExtractor(
                allow=r"^https://www.ford.com/content/brand_ford/en_us/brand/dealerships/dealer-details/.*.html$",
            ),
            callback="parse_sd",
        ),
    ]
