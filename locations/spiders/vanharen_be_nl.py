from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class VanharenBENLSpider(SitemapSpider, StructuredDataSpider):
    name = "vanharen_be_nl"
    item_attributes = {"brand": "vanHaren", "brand_wikidata": "Q62390668"}
    sitemap_urls = ["https://stores.vanharen.nl/sitemap.xml"]
    sitemap_rules = [(r"-\d+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_SHOES, item)
        yield item
