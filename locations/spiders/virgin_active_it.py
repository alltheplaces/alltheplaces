from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories
from locations.spiders.virgin_active_bw_na_za import VIRGIN_ACTIVE_SHARED_ATTRIBUTES
from locations.hours import DAYS_IT


class VirginActiveIT(CrawlSpider, StructuredDataSpider):
    name = "virgin_active_it"
    item_attributes = VIRGIN_ACTIVE_SHARED_ATTRIBUTES
    allowed_domains = ["www.virginactive.it"]
    start_urls = ["https://www.virginactive.it/club"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/club/[-\w]+/[-\w]+$"),
            follow=True,
        ),
    ]
    # days = DAYS_IT
    time_format = "%H.%M"
    wanted_types = ["ExerciseGym"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data):
        item["branch"] = item.pop("name")
        item["image"] = item["image"].split("?")[0]
        yield item
