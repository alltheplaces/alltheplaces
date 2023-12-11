from locations.categories import Categories, apply_category
from locations.storefinders.sweetiq import SweetIQSpider


class UltaBeautyUSSpider(SweetIQSpider):
    name = "ulta_beauty_us"
    item_attributes = {"brand": "Ulta Beauty", "brand_wikidata": "Q7880076"}
    start_urls = ["https://www.ulta.com/stores"]

    def parse_item(self, item, location):
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
