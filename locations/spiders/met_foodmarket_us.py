"""Spider for Met Foodmarket stores."""

from locations.storefinders.associated_supermarket_group import AssociatedSupermarketGroupSpider


class MetFoodmarketUSSpider(AssociatedSupermarketGroupSpider):
    """Spider for Met Foodmarket stores."""

    name = "met_foodmarket_us"
    item_attributes = {"brand": "Met Foodmarket", "brand_wikidata": "Q6822231"}
    start_urls = ["https://www.metfoods.com/locations"]
