from locations.playwright_spider import PlaywrightSpider
from locations.spiders.forever_new_au_nz import FOREVER_NEW_SHARED_ATTRIBUTES, ForeverNewAUNZSpider


class EverNewCASpider(ForeverNewAUNZSpider, PlaywrightSpider):
    name = "ever_new_ca"
    item_attributes = {**FOREVER_NEW_SHARED_ATTRIBUTES, "brand": "Ever New"}
    start_urls = [
        "https://www.evernew.ca/locator/index/search/?address=vancouver&components[country]=CA&radius=10000000&type=all",
    ]
    requires_proxy = True
