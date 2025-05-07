"""Spider for Met Foodmarket stores."""

from locations.storefinders.associated_supermarket_group import AssociatedSupermarketGroupSpider


class MetFoodmarketSpider(AssociatedSupermarketGroupSpider):
    """Spider for Met Foodmarket stores."""

    name = "met_foodmarket"
    item_attributes = {"brand": "Met Foodmarket", "brand_wikidata": "Q6822231"}
    start_urls = ["https://www.metfoods.com/locations"]
