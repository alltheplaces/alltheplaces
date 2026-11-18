from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MdaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mda_fr"
    item_attributes = {"brand": "MDA", "brand_wikidata": "Q121069178"}
    sitemap_urls = ["https://magasins.mda-electromenager.com/sitemap.xml"]
    sitemap_rules = [(r"com/(\d+)-mda-[^/]+$", "parse")]
    wanted_types = ["LocalBusiness"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = (item.pop("name") or "").removeprefix("MDA ")
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
