from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LaPlaceSpider(SitemapSpider, StructuredDataSpider):
    name = "la_place"
    item_attributes = {"brand":"La Place","brand_wikidata":"Q2041183"}
    sitemap_urls = ["https://www.laplace.com/sitemap.xml"]
    sitemap_rules = [("/locaties/la-place-", "parse")]
    search_for_facebook = False
    search_for_twitter = False
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("La Place ")
        apply_category(Categories.RESTAURANT, item)
        yield item