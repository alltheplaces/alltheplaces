from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class WesternDentalUSSpider(CrawlSpider, StructuredDataSpider):
    name = "western_dental_us"
    item_attributes = {
        "brand": "Western Dental",
        "brand_wikidata": "Q64211989",
    }
    allowed_domains = ["www.westerndental.com"]
    start_urls = ["https://www.westerndental.com/en-us/find-a-location/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.westerndental.com/en-us/find-a-location/[\w.-]+/$"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"https://www.westerndental.com/en-us/find-a-location/[\w.-]+/[\w.-]+/$"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"https://www.westerndental.com/en-us/find-a-location/[\w.-]+/[\w.-]+/[\w.-]+/$"),
            callback="parse",
        ),
    ]
    search_for_facebook = False
    time_format = "%I:%M%p"

    def post_process_item(self, item, response, ld_data):
        item["ref"] = response.url
        apply_category(Categories.DENTIST, item)
        yield item
