import chompjs
import scrapy

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser


class PizzaHutCLSpider(scrapy.Spider):
    name = "pizza_hut_cl"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615", "extras": Categories.RESTAURANT.value}
    start_urls = ["https://www.pizzahut.cl/es/store-locator.html"]

    def parse(self, response, **kwargs):
        for store in chompjs.parse_js_object(response.xpath('//script[contains(text(), "chainStores")]/text()').get())[
            "chainStores"
        ]["msg"]:
            store["address"].pop("city", "")  # city data not reliable,for many POIs it is "Santa Monica, CA, USA"
            store.update(store["address"].pop("latLng", {}))
            item = DictParser.parse(store)
            item["name"] = store.get("title", {}).get("es_ES")
            item["street_address"] = store["address"].get("formatted")
            item["website"] = f'https://www.pizzahut.cl/es/store-locator/{item["name"].lower().replace(" ", "_")}.html'
            apply_yes_no(Extras.DELIVERY, item, store.get("deliveryAllowed"))
            apply_yes_no(Extras.TAKEAWAY, item, store.get("pickUpAllwed") or store.get("pickUpAllowed"))
            yield item
