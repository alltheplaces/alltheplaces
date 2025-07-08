from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CircleKDKIESpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k_dk_ie"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = [
        "https://www.circlek.dk/stations",
        "https://www.circlek.ie/stations",
    ]
    rules = [Rule(LinkExtractor(allow="/station/"), callback="parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "CIRCLE K " in item["name"]:
            extract_google_position(item, response)
            item["country"] = "DK" if ".dk" in response.url else "IE"
            apply_category(Categories.FUEL_STATION, item)
            yield item
