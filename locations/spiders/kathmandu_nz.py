from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.storefinders.amai_promap import AmaiPromapSpider


class KathmanduNZSpider(AmaiPromapSpider, PlaywrightSpider):
    name = "kathmandu_nz"
    item_attributes = {"brand": "Kathmandu", "brand_wikidata": "Q1736294"}
    start_urls = ["https://www.kathmandu.co.nz/pages/stores"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
