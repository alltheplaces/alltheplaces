"""Spider for Associated Supermarket stores."""

from locations.storefinders.associated_supermarket_group import AssociatedSupermarketGroupSpider


class AssociatedSupermarketSpider(AssociatedSupermarketGroupSpider):
    """Spider for Associated Supermarket stores."""

    name = "associated_supermarket"
    item_attributes = {"brand": "Associated Supermarket", "brand_wikidata": "Q4809251"}
    start_urls = ["https://www.shopassociated.com/locations/"]
