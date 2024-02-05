import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.central_england_cooperative import COOP_FOOD, COOP_FUNERALCARE, set_operator

CHELMSFORD_STAR_COOP = {"brand": "Chelmsford Star Co-operative Society", "brand_wikidata": "Q5089972"}


class ChelmsfordStarCoopGBSpider(Spider):
    name = "chelmsford_star_coop_gb"
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
                item.update(COOP_FOOD)
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif any(cat["name"] == "Funeral" for cat in store["categories"]):
                item.update(COOP_FUNERALCARE)
                apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)
            elif any(cat["name"] == "Travel" for cat in store["categories"]):
                item["brand"] = "Coop Travel"
                apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
            elif any(cat["name"] == "Department store (Quadrant)" for cat in store["categories"]):
                item["brand"] = "Quadrant"
                apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            set_operator(CHELMSFORD_STAR_COOP, item)

            yield item
