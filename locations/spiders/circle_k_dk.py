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

    def pre_process_data(self, ld_data: dict, **kwargs):
        rules = ld_data.get("openingHours") or []
        for idx, rule in enumerate(rules):
            if len(rule) == 2:
                rules[idx] = "{} 00:00-24:00".format(rule)
        ld_data["openingHours"] = rules

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)
        yield item
