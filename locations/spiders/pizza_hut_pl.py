from unidecode import unidecode

from locations.categories import Categories
from locations.storefinders.amrest_eu import AmrestEUSpider


class PizzaHutPLSpider(AmrestEUSpider):
    name = "pizza_hut_pl"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615", "extras": Categories.FAST_FOOD.value}
    api_brand_key = "PH"
    api_brand_country_key = "PH_PL"
    api_source = "WEB"
    api_auth_source = "WEB_PH"
    api_channel = "TAKEAWAY"

<<<<<<< HEAD
    def parse_item(self, item, location):
=======
    def post_process_item(self, item, response, location):
>>>>>>> master
        item["branch"] = item.pop("name").removeprefix("Pizza Hut ")
        item["website"] = (
            "https://pizzahut.pl/en/restaurants/"
            + item["ref"]
            + "-"
            + unidecode(location["name"]).lower().replace(" ", "-")
        )
        yield item
