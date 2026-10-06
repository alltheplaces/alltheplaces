from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EarlySettlerSpider(SitemapSpider, StructuredDataSpider):
    name = "early_settler"
    item_attributes = {"brand": "Early Settler", "brand_wikidata": "Q111080173"}
    sitemap_urls = ["https://earlysettler.com.au/sitemap.xml", "https://earlysettler.co.nz/sitemap.xml"]
    sitemap_follow = [r"/sitemap_pages_"]
    sitemap_rules = [(r"/pages/", "parse_sd")]
    wanted_types = ["FurnitureStore"]
    search_for_email = False
    search_for_facebook = False
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if "Opening Soon" in item["name"] or "Coming Soon" in item["name"]:
            return

        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_FURNITURE, item)

        yield item
