from locations.categories import Categories
from locations.storefinders.amrest_eu import AmrestEUSpider


class LaTagliatellaESSpider(AmrestEUSpider):
    name = "la_tagliatella_es"
    item_attributes = {"brand": "La Tagliatella", "brand_wikidata": "Q113426257", "extras": Categories.RESTAURANT.value}
    api_brand_country_key = "TAG_ES"
    api_source = "WEB"
    api_auth_source = "WEB_KFC"
    api_channel = "DINE_IN"

    def post_process_item(self, item, response, location):
        # storeLocatorUrl format vary for other Amrest brands
        item["website"] = location.get("storeLocatorUrl")
        item["branch"] = item.pop("name")
        yield item
