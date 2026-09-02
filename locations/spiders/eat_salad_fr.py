from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EatSaladFRSpider(SitemapSpider, StructuredDataSpider):
    name = "eat_salad_fr"
    item_attributes = {"brand": "Eat Salad", "brand_wikidata": "Q141214255"}
    sitemap_urls = ["https://commande.eatsalad.com/sitemap.xml"]
    sitemap_rules = [(r"https\:\/\/commande\.eatsalad\.com\/restaurants\/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness", "Restaurant", "FastFoodRestaurant"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
