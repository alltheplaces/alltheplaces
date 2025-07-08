from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class CircleKSESpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k_se"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.se/stations"]
    rules = [Rule(LinkExtractor(allow=r"/station/circle-k-[-\w]+/?$"), callback="parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)
        yield item
