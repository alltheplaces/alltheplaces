from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NoriskoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "norisko_fr"
    item_attributes = {"brand": "Norisko", "brand_wikidata": "Q141159455"}
    sitemap_urls = ["https://www.dekra-norisko.fr/sitemap.xml"]
    sitemap_rules = [(r"https://www\.dekra-norisko\.fr/norisko/controle-technique/[^?]+", "parse_sd")]
    wanted_types = ["AutoRepair"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.VEHICLE_INSPECTION, item)
        
        generic_facebook_urls = (
            "https://www.facebook.com/dekra.norisko.officiel/",
            "https://www.facebook.com/dekra.automotive"
        )
        
        if item.get("facebook") in generic_facebook_urls:
            item.pop("facebook", None)
            
        yield item
