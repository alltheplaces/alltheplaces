from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KidStrongUSCASpider(SitemapSpider, StructuredDataSpider):
    name = "kid_strong_us_ca"
    item_attributes = {"brand": "KidStrong", "brand_wikidata": "Q125705878"}
    sitemap_urls = ["https://www.kidstrong.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/?$", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").rpartition("/")[2]
        item["branch"] = item.pop("name").removeprefix("KidStrong ")
        item["website"] = response.url
        apply_category(Categories.GYM, item)
        yield item
