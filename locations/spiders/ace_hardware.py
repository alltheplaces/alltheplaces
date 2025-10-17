from locations.storefinders.kibo import KiboSpider
from locations.user_agents import BROWSER_DEFAULT


class AceHardwareSpider(KiboSpider):
    name = "ace_hardware"
    item_attributes = {"brand": "Ace Hardware", "brand_wikidata": "Q4672981"}
    start_urls = ["https://www.acehardware.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True
