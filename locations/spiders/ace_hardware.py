from locations.storefinders.kibo import KiboSpider


class AceHardwareSpider(KiboSpider):
    name = "ace_hardware"
    item_attributes = {"brand": "Ace Hardware", "brand_wikidata": "Q4672981"}
    start_urls = ["https://www.acehardware.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    user_agent = None
    requires_proxy = True
