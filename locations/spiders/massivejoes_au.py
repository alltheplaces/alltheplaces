from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MassivejoesAUSpider(WPStoreLocatorSpider):
    name = "massivejoes_au"
    item_attributes = {"brand": "MassiveJoes", "brand_wikidata": "Q117746887"}
    allowed_domains = ["massivejoes.com"]
    time_format = "%I:%M %p"
