from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FarmfoodsSKSpider(WPStoreLocatorSpider):
    name = "farmfoods_sk"
    item_attributes = {
        "brand_wikidata": "Q116867227",
        "brand": "FARMFOODS",
    }
    allowed_domains = [
        "predajne.farmfoods.sk",
    ]
