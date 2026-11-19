from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class LAtelierDuSourcilFRSpider(UberallSpider):
    name = "l_atelier_du_sourcil_fr"
    item_attributes = {"brand": "L'Atelier du Sourcil", "brand_wikidata": "Q128618614"}
    key = "lBz2BsJRajBjVD3RwTVDUfKv0MtTHD"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix("L'Atelier du Sourcil - ")
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
