import html
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class FavoriteChickenGBSpider(CrawlSpider, StructuredDataSpider):
    name = "favorite_chicken_gb"
    item_attributes = {"brand_wikidata": "Q120070660"}
    start_urls = ["https://favorite.co.uk/store-finder/gb.html"]
    rules = [
        Rule(LinkExtractor(allow=r"^https://favorite.co.uk/store-finder/gb/[-\w]+.html$")),
        Rule(LinkExtractor(allow=r"^https://favorite.co.uk/store-finder/gb/[-\w]+/[-\w]+.html$")),
        Rule(LinkExtractor(allow=r"^https://favorite.co.uk/store-finder/favorite-"), "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(
            r"DisplayCoordinate\":{\"latitude\":(-?\d+\.\d+),\"longitude\":(-?\d+\.\d+)}}", response.text
        ):
            item["lat"], item["lon"] = m.groups()
        item["name"] = html.unescape(item["name"])
        yield item
