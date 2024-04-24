from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SanelNAPASpider(WPStoreLocatorSpider):
    name = "sanel_napa"
    item_attributes = {
        "brand_wikidata": "Q122564780",
        "brand": "Sanel NAPA",
    }
    allowed_domains = [
        "sanelnapa.com",
    ]
    time_format = "%I:%M %p"
