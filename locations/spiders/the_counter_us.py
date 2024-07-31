from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class TheCounterUSSpider(CrawlSpider, StructuredDataSpider):
    name = "the_counter_us"
    item_attributes = {"brand": "The Counter", "brand_wikidata": "Q7727763"}
    allowed_domains = ["www.thecounter.com"]
    start_urls = ["https://www.thecounter.com/locator/index.php?brand=32&pagesize=50&q=o"]
    rules = [Rule(LinkExtractor(allow=(r"/stores/[\w-]+/\d+$",)), callback="parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data):
        del item["name"]
        del item["image"]
        yield item
