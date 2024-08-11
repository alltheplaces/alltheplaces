from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ChocolateCompanyNLSpider(WPStoreLocatorSpider):
    name = "chocolate_company_nl"
    item_attributes = {
        "brand_wikidata": "Q108926938",
        "brand": "Chocolate Company",
    }
    allowed_domains = [
        "choco.piranha-dev.online",
    ]
