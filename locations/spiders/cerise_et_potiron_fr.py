from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wordpress_heron_foods_spider import WordpressHeronFoodsSpider


class CeriseEtPotironFRSpider(WordpressHeronFoodsSpider):
    name = "cerise_et_potiron_fr"
    item_attributes = {"brand": "Cerise et Potiron", "brand_wikidata": "Q91634572"}
    domain = "www.cerise-et-potiron.fr"
    radius = 600
    lat = 45.7490921
    lon = 4.8419781

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_GREENGROCER, item)
        yield item
