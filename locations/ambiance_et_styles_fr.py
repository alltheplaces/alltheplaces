from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AmbianceEtStylesFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ambiance_et_styles_fr"
    item_attributes = {"brand": "Ambiance & Styles", "brand_wikidata": "Q141345963"}
    sitemap_urls = ["https://ambianceetstyles.com/storage/sitemap.xml"]
    sitemap_rules = [(r"https://ambianceetstyles.com/magasins/ambiance-styles.*", "parse_sd")]
    wanted_types = ["Store"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/ambianceetstyles":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("Ambiance & Styles ")
        
        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
        yield item
