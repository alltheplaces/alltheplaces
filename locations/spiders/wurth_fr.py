from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WurthFRSpider(SitemapSpider, StructuredDataSpider):
    name = "wurth_fr"
    item_attributes = {"brand": "Würth", "brand_wikidata": "Q679750"}
    sitemap_urls = ["https://magasins.wurth.fr/locationsitemap1.xml"]
    sitemap_rules = [(r"https://magasins.wurth.fr/.*", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image", "facebook", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Würth ")
        apply_category(Categories.SHOP_HARDWARE, item)
        yield item
