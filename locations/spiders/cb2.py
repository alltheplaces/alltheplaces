from locations.categories import Categories
from locations.spiders.crateandbarrel import CrateandbarrelSpider


class Cb2Spider(CrateandbarrelSpider):
    name = "cb2"
    allowed_domains = ["www.cb2.com"]
    item_attributes = {
        "brand": "CB2",
        "name": "CB2",
        "brand_wikidata": "Q113164236",
        "extras": Categories.SHOP_FURNITURE.value,
    }
    start_urls = ["https://www.cb2.com/stores/list-state/retail-stores"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        for item in super().post_process_item(item, response, ld_data, **kwargs):
            item["branch"] = item["branch"].removeprefix("CB2 ")
            yield item
