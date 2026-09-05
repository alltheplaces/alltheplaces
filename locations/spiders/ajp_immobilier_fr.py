from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AjpImmobilierFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ajp_immobilier_fr"
    item_attributes = {"brand": "AJP Immobilier", "brand_wikidata": "Q141301527"}
    sitemap_urls = ["https://www.ajp-immobilier.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.ajp-immobilier.com/agence-immobiliere/.*", "parse_sd")]
    wanted_types = ["RealEstateAgent"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/ajpimmobilierfrance":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("AJP Immobilier ")
    
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
