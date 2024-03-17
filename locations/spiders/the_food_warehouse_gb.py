from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TheFoodWarehouseGBSpider(Spider):
    name = "the_food_warehouse_gb"
    item_attributes = {
        "brand": "The Food Warehouse",
        "brand_wikidata": "Q87263899",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.thefoodwarehouse.com"]
    start_urls = ["https://www.thefoodwarehouse.com/assets/foodwarehouse/ajax/"]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            if "CLOSED" in item["name"].upper() or "COMING SOON" in item["name"].upper():
                continue
            item["ref"] = store["storeNo"]
            item["website"] = "https://www.thefoodwarehouse.com/" + store["url"]
            item["phone"] = store.get("store-number")
            item["addr_full"] = (
                item["addr_full"].replace("<br>", "").replace("<br />", "").replace("<p>", "").replace("</p>", "")
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(store.get("opening-times", ""))
            yield item
