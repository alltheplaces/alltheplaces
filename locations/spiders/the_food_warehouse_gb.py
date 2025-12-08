from scrapy import Selector, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class TheFoodWarehouseGBSpider(Spider):
    name = "the_food_warehouse_gb"
    item_attributes = {
        "brand": "The Food Warehouse",
        "brand_wikidata": "Q87263899",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.thefoodwarehouse.com"]
    start_urls = ["https://www.thefoodwarehouse.com/assets/foodwarehouse/ajax/"]
    no_refs = True  # https://github.com/alltheplaces/alltheplaces/issues/8237

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            if "CLOSED" in item["name"].upper() or "COMING SOON" in item["name"].upper():
                continue
            if store["url"] != "/store-locator/default-store":
                item["website"] = "https://www.thefoodwarehouse.com" + store["url"]
            item["branch"] = item.pop("name").removesuffix(" - Now Open")
            item["phone"] = store.get("store-number")
            item["addr_full"] = merge_address_lines(Selector(text=item["addr_full"]).xpath("//text()").getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(store.get("opening-times", ""))
            yield item
