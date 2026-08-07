from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PenningtonsCASpider(SitemapSpider, StructuredDataSpider):
    name = "penningtons_ca"
    item_attributes = {"brand": "Penningtons", "brand_wikidata": "Q16956527"}
    sitemap_urls = ["https://locations.penningtons.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["ClothingStore"]
    time_format = "%I:%M %p"
    search_for_facebook = False
    search_for_twitter = False
    search_for_image = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name")
        item.pop("image", None)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
