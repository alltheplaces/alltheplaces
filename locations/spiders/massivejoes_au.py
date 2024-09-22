from locations.categories import Categories
from locations.storefinders.storeify import StoreifySpider


class MassivejoesAUSpider(StoreifySpider):
    name = "massivejoes_au"
    item_attributes = {
        "brand": "MassiveJoes",
        "brand_wikidata": "Q117746887",
        "extras": Categories.SHOP_NUTRITION_SUPPLEMENTS.value,
    }
    api_key = "58d7df-3.myshopify.com"
    # https://sl.storeify.app/js/stores/58d7df-3.myshopify.com/storeifyapps-storelocator-geojson.js?v=1717415092