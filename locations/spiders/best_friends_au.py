from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class BestFriendsAUSpider(CrawlSpider, StructuredDataSpider):
    name = "best_friends_au"
    item_attributes = {"brand": "Best Friends", "brand_wikidata": "Q106540748"}
    start_urls = ["https://www.bestfriendspets.com.au/store-locator"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.bestfriendspets.com.au/store-locator/.*$"),
            callback="parse_sd",
        ),
    ]
