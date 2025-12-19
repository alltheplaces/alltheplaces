from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CricketWirelessSpider(CrawlSpider, StructuredDataSpider):
    name = "cricket_wireless"
    item_attributes = {"brand": "Cricket Wireless", "brand_wikidata": "Q5184987"}
    start_urls = ["https://www.cricketwireless.com/stores/index.html"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//a[contains(@class, "Link orc-link standalone flex gap-1 w-fit")]')),
        Rule(LinkExtractor(restrict_xpaths='//a[contains(@class, "Link orc-link standalone flex gap-1 w-fit")]')),
        Rule(
            LinkExtractor(
                restrict_xpaths='//a[contains(@class, "Link orc-link standalone flex items-center gap-1 w-fit")]',
                deny_domains=["www.google.com"],
            ),
            callback="parse",
        ),
    ]
