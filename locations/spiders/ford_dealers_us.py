from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FordDealersUSSpider(CrawlSpider, StructuredDataSpider):
    name = "ford_dealers_us"
    item_attributes = {
        "brand": "Ford",
        "brand_wikidata": "Q44294",
    }
    start_urls = ["https://www.ford.com/dealerships/dealer-directory/browse-all/"]
    wanted_types = ["AutoDealer"]
    json_parser = "chompjs"
    rules = [
        Rule(
            LinkExtractor(allow=r"^https://www.ford.com/dealerships/dealer-directory/"),
        ),
        Rule(
            LinkExtractor(
                allow=(
                    r"^https://www.ford.com/content/brand_ford/en_us/brand/dealerships/dealer-details/.*.html$",
                    r"^https://www.ford.com/dealerships/dealer-details/.*$",
                ),
            ),
            callback="parse_sd",
        ),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CAR, item)

        yield item
