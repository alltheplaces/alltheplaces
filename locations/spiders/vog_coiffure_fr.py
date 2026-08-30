from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class VogCoiffureFRSpider(SitemapSpider, StructuredDataSpider):
    name = "vog_coiffure_fr"
    item_attributes = {"brand": "Vog Coiffure", "brand_wikidata": "Q141223643"}
    sitemap_urls = ["https://salons.vog.fr/sitemap.xml"]
    sitemap_rules = [(r"https://salons\.vog\.fr/\d+/.+$", "parse_sd")]
    wanted_types = ["HairSalon"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_HAIRDRESSER, item)  
        yield item
