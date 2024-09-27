from unidecode import unidecode

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingNCSpider(JSONBlobSpider):
    name = "burger_king_nc"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.burgerking.nc/wp-content/themes/burgerking/json-data/stores.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace("BURGER KING® ", "")
        item["website"] = (
            f"https://www.burgerking.nc/restaurants/burger-king-{unidecode(item['branch'].replace(" ", "-").lower())}/"
        )
        yield item
        # TODO more info on individual pages, but doesn't seem worth html parsing for 4 locations
