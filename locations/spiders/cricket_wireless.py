from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CricketWirelessSpider(CrawlSpider, StructuredDataSpider):
    name = "cricket_wireless"
    item_attributes = {"brand": "Cricket Wireless", "brand_wikidata": "Q5184987"}
    start_urls = ["https://www.cricketwireless.com/stores/index.html"]
    rules = [
        Rule(
            LinkExtractor(
                restrict_xpaths='//a[contains(@class, "Link text-base hover:underline a4-Link flex gap-1 w-fit")]'
            )
        ),
        Rule(
            LinkExtractor(
                restrict_xpaths='//a[contains(@class, "Link text-base hover:underline a4-Link flex gap-1 w-fit")]'
            )
        ),
        Rule(
            LinkExtractor(
                restrict_xpaths='//a[contains(@class, "Link flex items-center gap-1 w-fit text-brand-blue a4-Link")]',
                deny_domains=["www.google.com"],
            ),
            callback="parse",
        ),
    ]
