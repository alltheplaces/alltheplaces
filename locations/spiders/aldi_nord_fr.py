from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class AldiNordFRSpider(UberallSpider):
    name = "aldi_nord_fr"
    item_attributes = {"brand_wikidata": "Q41171373"}
    key = "ALDINORDFR_Mmljd17th8w26DMwOy4pScWk4lCvj5"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix("ALDI ")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
