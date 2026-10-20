from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ClassicCollisionUSSpider(SitemapSpider, StructuredDataSpider):
    name = "classic_collision_us"
    item_attributes = {"brand": "Classic Collision", "brand_wikidata": "Q122760989"}
    sitemap_urls = ["https://classiccollision.com/wpsl_stores-sitemap.xml"]
    wanted_types = ["AutoRepair"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = response.xpath('//span[@class="locnamecol"]/text()').get()
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
