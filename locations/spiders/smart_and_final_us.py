from locations.categories import Categories
from locations.storefinders.wakefern import WakefernSpider


# Not owned by Wakefern (as far as I can tell), but seems to use the same software
class SmartAndFinalUSSpider(WakefernSpider):
    name = "smart_and_final_us"
    item_attributes = {
        "brand": "Smart & Final",
        "brand_wikidata": "Q7543916",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://www.smartandfinal.com/"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix(f"{location['retailerStoreId']} - ")
        yield from super().post_process_item(item, response, location)
