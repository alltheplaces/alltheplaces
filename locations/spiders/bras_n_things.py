from locations.storefinders.limesharp_store_locator import LimesharpStoreLocatorSpider


class BrasNThingsSpider(LimesharpStoreLocatorSpider):
    name = "bras_n_things"
    item_attributes = {"brand": "Bras N Things", "brand_wikidata": "Q120669960"}
    allowed_domains = [
        # All of these allowed domains return the same store data.
        "www.brasnthings.com",
        # "www.brasnthings.co.nz",
        # "www.brasnthings.co.za",
    ]
