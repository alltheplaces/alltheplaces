from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BureauValleeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "bureau_vallee_fr"
    item_attributes = {"brand": "Bureau Vallée", "brand_wikidata": "Q18385014"}
    sitemap_urls = ["https://magasins.bureau-vallee.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"https://magasins\.bureau-vallee\.fr/fr/france-FR/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness", "OfficeEquipmentStore"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_STATIONERY, item)
        yield item
