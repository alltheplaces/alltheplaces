from unidecode import unidecode

from locations.categories import Categories
from locations.storefinders.amrest_eu import AmrestEUSpider


class PizzaHutCZSpider(AmrestEUSpider):
    name = "pizza_hut_cz"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615", "extras": Categories.FAST_FOOD.value}
    api_brand_key = "PH"
    api_brand_country_key = "PH_CZ"
    api_source = "WEB"
    api_auth_source = "WEB_PH"
    api_channel = "TAKEAWAY"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix("Pizza Hut ")
        item["website"] = (
            "https://pizzahut.cz/en/restaurants/"
            + item["ref"]
            + "-"
            + unidecode(location["name"]).lower().replace(" ", "-")
        )
        yield item
