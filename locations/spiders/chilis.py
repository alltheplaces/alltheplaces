from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ChilisSpider(CrawlSpider, StructuredDataSpider):
    name = "chilis"
    item_attributes = {"brand": "Chili's", "brand_wikidata": "Q1072948"}
    allowed_domains = ["chilis.com"]
    download_delay = 0.5
    start_urls = ["https://www.chilis.com/locations/us/all"]
    rules = (
        Rule(
            LinkExtractor(restrict_xpaths='//div[contains(@class, "city-locations")]//a[@class="city-link"]'),
            follow=True,
            callback="parse_city",
        ),
        Rule(
            LinkExtractor(restrict_xpaths='//a[text()="Details"]'),
            follow=True,
            callback="parse_sd",
        ),
    )

    def post_process_item(self, item, response, ld_data):
        item["ref"] = ld_data["branchCode"]
        yield item
