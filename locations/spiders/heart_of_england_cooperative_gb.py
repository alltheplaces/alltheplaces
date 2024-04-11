from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.central_england_cooperative import COOP_FOOD, set_operator
from locations.storefinders.super_store_finder import SuperStoreFinderSpider

HEART_OF_ENGLAND_COOP = {"brand": "Heart of England Co-operative Society", "brand_wikidata": "Q5692254"}


class HeartOfEnglandCooperativeGBSpider(SuperStoreFinderSpider):
    name = "heart_of_england_cooperative_gb"
    start_urls = ["https://www.cawtest.com/heartofengland/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php"]

    def parse_item(self, item: Feature, location: Selector, **kwargs):
        item["branch"] = item.pop("name")

        item.update(COOP_FOOD)
        set_operator(HEART_OF_ENGLAND_COOP, item)
        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
