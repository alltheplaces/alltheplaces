from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ElsieSanteFRSpider(SitemapSpider, StructuredDataSpider):
    name = "elsie_sante_fr"
    item_attributes = {"brand": "Elsie Santé", "brand_wikidata": "Q127603214"}
    sitemap_urls = ["https://pharmacie.elsie-sante.fr/locationsitemap1.xml"]
    sitemap_rules = [(r"https://pharmacie.elsie-sante.fr/+", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.PHARMACY, item)
        yield item
