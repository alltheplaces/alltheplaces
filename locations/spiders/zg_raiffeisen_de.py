from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class ZgRaiffeisenDESpider(UberallSpider):
    """Spider for ZG Raiffeisen agrarian stores (Germany).
    Closes #7034
    """

    name = "zg_raiffeisen_de"
    item_attributes = {"brand": "ZG Raiffeisen", "brand_wikidata": "Q136135"}
    key = "ooHwNN7SQvTWSMqR5bn1F1G0aGuTSu"

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_AGRARIAN, item)
        yield item
