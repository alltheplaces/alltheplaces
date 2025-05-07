"""Spider for Pioneer Supermarket stores."""

from locations.storefinders.associated_supermarket_group import AssociatedSupermarketGroupSpider


class PioneerSupermarketUSSpider(AssociatedSupermarketGroupSpider):
    """Spider for Pioneer Supermarket stores."""

    name = "pioneer_supermarket_us"
    item_attributes = {"brand": "Pioneer Supermarket"}
    start_urls = ["https://www.pioneersupermarkets.com/locations/"]
