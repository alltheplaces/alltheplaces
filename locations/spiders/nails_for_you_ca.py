from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class NailsforYouCASpider(AgileStoreLocatorSpider):
    name = "nails_for_you_ca"
    item_attributes = {
        "brand_wikidata": "Q123410053",
        "brand": "Nails for You",
    }
    allowed_domains = [
        "nailsforyou.ca",
    ]
