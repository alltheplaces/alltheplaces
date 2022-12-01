from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class IntratuinSpider(CrawlSpider, StructuredDataSpider):
    name = "intratuin"
    item_attributes = {"brand": "Intratuin", "brand_wikidata": "Q2927176"}
    start_urls = ["https://www.intratuin.nl/winkels"]
    rules = [Rule(LinkExtractor(allow="intratuin-"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)

        yield item
