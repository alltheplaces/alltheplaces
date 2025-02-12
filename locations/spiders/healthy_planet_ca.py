from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class HealthyPlanetCASpider(AmastyStoreLocatorSpider):
    name = "healthy_planet_ca"
    item_attributes = {
        "brand_wikidata": "Q113001393",
        "brand": "Healthy Planet",
    }
    allowed_domains = [
        "www.healthyplanetcanada.com",
    ]
