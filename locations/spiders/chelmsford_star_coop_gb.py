import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ChelmsfordStarCoopGBSpider(Spider):
    name = "chelmsford_star_coop_gb"
    item_attributes = {"brand": "Chelmsford Star Coop", "brand_wikidata": "Q5089972"}
    start_urls = ["https://www.chelmsfordstar.coop/find-us/"]

    def parse(self, response):
        script = response.xpath('//script[contains(text(), "var map5 =")]/text()').get()
        script = (
            script.replace("jQuery(document).ready(function($) {", "")
            .replace("});", "")
            .replace('decoding="async"', "")
        )

        stores = chompjs.parse_js_object(script)["places"]

        for store in stores:
            store.update(store.pop("location"))
            store["website"] = store["redirect_permalink"]
            store["phone"] = store["extra_fields"]["%store_telephone%"]

            item = DictParser.parse(store)

            if any(cat["name"] == "Food" for cat in store["categories"]):
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif any(cat["name"] == "Funeral" for cat in store["categories"]):
                apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)
            elif any(cat["name"] == "Travel" for cat in store["categories"]):
                apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
            elif any(cat["name"] == "Department store (Quadrant)" for cat in store["categories"]):
                apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            yield item
