from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.storefinders.kibo import KiboSpider
from locations.user_agents import BROWSER_DEFAULT


class AceHardwareUSSpider(KiboSpider, PlaywrightSpider):
    name = "ace_hardware_us"
    item_attributes = {"brand": "Ace Hardware", "brand_wikidata": "Q4672981"}
    start_urls = ["https://www.acehardware.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}
