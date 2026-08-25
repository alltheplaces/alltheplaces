from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AuVideGrenierFRSpider(SitemapSpider, StructuredDataSpider):
    name = "au_vide_grenier_fr"
    item_attributes = {"brand": "Au Vide Grenier", "brand_wikidata": "Q141175815"}
    sitemap_urls = ["https://auvidegrenier.fr/sitemap/shops.xml"]
    sitemap_rules = [(r"https:\/\/auvidegrenier\.fr\/magasins\/", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Au Vide Grenier ")
        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
