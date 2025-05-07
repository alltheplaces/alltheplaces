"""Spider for Compare Foods stores."""

from locations.storefinders.associated_supermarket_group import AssociatedSupermarketGroupSpider


class CompareFoodsSpider(AssociatedSupermarketGroupSpider):
    """Spider for Compare Foods stores."""

    name = "compare_foods"
    item_attributes = {"brand": "Compare Foods"}
    start_urls = ["https://www.shopcomparefoods.com/locations/"]
