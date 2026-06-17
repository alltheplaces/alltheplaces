from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JustparkGBSpider(SitemapSpider, StructuredDataSpider):
    name = "justpark_gb"
    item_attributes = {"brand": "JustPark", "brand_wikidata": "Q17143517"}
    allowed_domains = ["justpark.com"]
    sitemap_urls = ["https://www.justpark.com/sitemap.xml"]
    sitemap_follow = ["uk_listings_"]
    sitemap_rules = [("/uk/parking/", "parse_sd")]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.PARKING, item)
        yield item
