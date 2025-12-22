from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.cineworld_gb_je import CineworldGBJESpider
from locations.spiders.millies_gb import MilliesGBSpider
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BaskinRobbinsGBIEJESpider(AgileStoreLocatorSpider):
    name = "baskin_robbins_gb_ie_je"
    item_attributes = {"brand": "Baskin-Robbins", "brand_wikidata": "Q584601"}
    allowed_domains = ["baskinrobbins.co.uk"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "Wraps & Wings" in item["name"]:
            item["brand"] = "Wraps & Wings"
            item["brand_wikidata"] = "Q137537572"
            apply_category(Categories.FAST_FOOD, item)
        if "(Cineworld)" in item["name"]:
            item["located_in"] = CineworldGBJESpider.item_attributes["brand"]
            item["located_in_wikidata"] = CineworldGBJESpider.item_attributes["brand_wikidata"]
            item["name"] = item["name"].replace("(Cineworld)", "").strip()
        elif "(Millies Cookies)" in item["name"]:
            item["located_in"] = MilliesGBSpider.item_attributes["brand"]
            item["located_in_wikidata"] = MilliesGBSpider.item_attributes["brand_wikidata"]
            item["name"] = item["name"].replace("(Millies Cookies)", "").strip()
        if item["phone"] and "333 003 3444" in item["phone"]:
            del item["phone"]
        item["branch"] = item.pop("name")

        yield item
