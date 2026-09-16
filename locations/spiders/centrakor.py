from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CentrakorSpider(SitemapSpider, StructuredDataSpider):
    name = "centrakor"
    item_attributes = {"brand": "Centrakor", "brand_wikidata": "Q64079345"}
    sitemap_urls = ["https://www.centrakor.com/sitemaps/default/stores-sitemap.xml"]
    sitemap_rules = [(r"/magasin-centrakor/", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        for prefix in ("Centrakor / ", "Centrakor ", "CENTRAKOR "):
            # Some franchisees submit their store's name in all caps
            if branch.startswith(prefix):
                branch = branch[len(prefix) :]
                break
        item["branch"] = branch

        if item.get("email") in ("adv.site@centrakor.com", "support.achat@cid-sa.com"):
            # Corporate/regional-office addresses shared across many stores, not location-specific
            item.pop("email")

        if item.get("image") and "logo" in item["image"]:
            # Generic brand logo used when a store hasn't uploaded its own photo
            item.pop("image")

        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
        yield item
