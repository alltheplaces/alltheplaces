from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class QBDBooksAUSpider(CrawlSpider, StructuredDataSpider):
    name = "qbd_books_au"
    item_attributes = {"brand": "QBD Books", "brand_wikidata": "Q118994358"}
    allowed_domains = ["www.qbd.com.au"]
    start_urls = ["https://www.qbd.com.au/locations/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.qbd\.com\.au\/locations\/[\w\-]+\/$"),
            callback="parse_sd",
            follow=False,
        )
    ]
    wanted_types = ["Store"]

    def post_process_item(self, item, response, ld_data):
        if "www.qbd.com.au" not in item.get("image", ""):
            item.pop("image")
        item.pop("facebook")
        item.pop("twitter")
        yield item
