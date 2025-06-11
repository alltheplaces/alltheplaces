"""Spider for Compare Foods stores."""

from locations.storefinders.associated_supermarket_group import AssociatedSupermarketGroupSpider


class CompareFoodsUSSpider(AssociatedSupermarketGroupSpider):
    """Spider for Compare Foods stores."""

    name = "compare_foods_us"
    item_attributes = {"brand": "Compare Foods"}
    start_urls = ["https://www.shopcomparefoods.com/locations/"]
