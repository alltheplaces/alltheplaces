from scrapy.linkextractors import LinkExtractor
from scrapy.settings.default_settings import RETRY_HTTP_CODES
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class FamilyDollarSpider(CrawlSpider, StructuredDataSpider):
    name = "family_dollar"
    item_attributes = {"brand": "Family Dollar", "brand_wikidata": "Q5433101"}
    allowed_domains = ["familydollar.com"]
    start_urls = ("https://locations.familydollar.com",)

    # site apparently uses 301 to mean temporary server error, which causes
    # scrapy to avoid repeating the request by default
    custom_settings = {
        "RETRY_HTTP_CODES": RETRY_HTTP_CODES + [301],
        "REDIRECT_ENABLED": False,
    }

    rules = [
        Rule(
            LinkExtractor(allow=[r"/\d+/$"], restrict_css=".itemlist"),
            callback="parse_sd",
        ),
        Rule(LinkExtractor(restrict_css=".itemlist")),
    ]

    def pre_process_data(self, ld_data):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, "%H:%M %p")
        del ld_data["openingHoursSpecification"]
        ld_data["openingHours"] = oh.as_opening_hours()
