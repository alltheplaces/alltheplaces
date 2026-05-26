from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TanningShopIESpider(SitemapSpider, StructuredDataSpider):
    name = "tanning_shop_ie"
    item_attributes = {"brand_wikidata": "Q123101132", "brand": "Tanning Shop"}
    sitemap_urls = ["https://thetanningshop.ie/locations-sitemap.xml"]
    sitemap_rules = [(r"/location/[^/]+/$", "parse_sd")]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("The Tanning Shop ")
        apply_category(Categories.SHOP_BEAUTY, item)

        yield item
