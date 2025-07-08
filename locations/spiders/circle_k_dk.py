from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CircleKDKSpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k_dk"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.dk/stations"]
    rules = [Rule(LinkExtractor(allow="/station/circle"), callback="parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)
        yield item
