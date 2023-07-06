import scrapy

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class TheFoodWarehouse(scrapy.Spider):
    name = "the_food_warehouse_gb"
    item_attributes = {
        "brand": "The Food Warehouse",
        "brand_wikidata": "Q87263899",
        "country": "GB",
    }
    start_urls = ["https://www.thefoodwarehouse.com/assets/foodwarehouse/ajax/"]

    def parse(self, response, **kwargs):
        for store in response.json():
            item = DictParser.parse(store)

            item["ref"] = store["storeNo"]

            item["website"] = "https://www.thefoodwarehouse.com/" + store["url"]
            item["phone"] = store.get("store-number")
            item["image"] = store["store-image"]
            item["addr_full"] = clean_address(
                item["addr_full"].replace("<br>", "").replace("<br />", "").replace("<p>", "").replace("</p>", "")
            )
            # TODO: Opening hours

            yield item
