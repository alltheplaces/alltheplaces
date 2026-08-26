from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class RemaxDESpider(StructuredDataSpider):
    name = "remax_de"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    start_urls = ["https://www.remax.de/en/real-estate-offices-agents"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
