from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class WebuyanycarGBSpider(CrawlSpider, StructuredDataSpider):
    name = "webuyanycar_gb"
    item_attributes = {"brand": "WeBuyAnyCar", "brand_wikidata": "Q7977432"}
    allowed_domains = ["www.webuyanycar.com"]
    start_urls = ["https://www.webuyanycar.com/branch-locator/"]
    rules = [
        Rule(
            LinkExtractor(allow=".*/branch-locator/.*"),
            callback="parse_sd",
            follow=False,
        )
    ]
    download_delay = 0.5

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        yield item
