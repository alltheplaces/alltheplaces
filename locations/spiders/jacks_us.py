from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JacksUSSpider(SitemapSpider, StructuredDataSpider):
    name = "jacks_us"
    item_attributes = {"brand": "Jack's", "brand_wikidata": "Q6110826"}
    drop_attributes = {"name"}
    sitemap_urls = ["https://locations.eatatjacks.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["FoodEstablishment"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if response.xpath('//*[contains(text(), "Coming Soon")]'):
            return
        extract_google_position(item, response)
        yield item
