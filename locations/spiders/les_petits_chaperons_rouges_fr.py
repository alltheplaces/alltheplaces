from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LesPetitsChaperonsRougesFRSpider(SitemapSpider, StructuredDataSpider):
    name = "les_petits_chaperons_rouges_fr"
    item_attributes = {"brand": "Les Petits Chaperons Rouges", "brand_wikidata": "Q130214582"}
    sitemap_urls = ["https://www.lpcr.fr/sitemap.xml"]
    sitemap_rules = [(r"https://www\.lpcr\.fr/.*creches/.+$", "parse_sd")]
    wanted_types = ["ChildCare"]
    drop_attributes = {"image", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.KINDERGARTEN, item)
        yield item
