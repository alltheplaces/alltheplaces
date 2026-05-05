from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FootasylumGBSpider(SitemapSpider, StructuredDataSpider):
    name = "footasylum_gb"
    item_attributes = {"brand": "Footasylum", "brand_wikidata": "Q126913565"}
    sitemap_urls = ["https://www.footasylum.com/ArticlesSiteMap.xml"]
    sitemap_rules = [("https://www.footasylum.com/store-locator/[^/]+/", "parse_sd")]
    requires_proxy = True
    wanted_types = ["Store"]
    drop_attributes = {"facebook", "image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        # opening hours are wrong in the structured data
        item.pop("opening_hours", None)

        apply_category(Categories.SHOP_SHOES, item)

        yield item
