from locations.storefinders.wp_store_locator import WPStoreLocatorSpider
from locations.hours import DAYS_EN


class LeaderBRSpider(WPStoreLocatorSpider):
    name = "leader_br"
    days = DAYS_EN
    item_attributes = {
        "brand_wikidata": "Q10316732",
        "brand": "Leader",
    }
    allowed_domains = [
        "institucional.lojasleader.com.br",
    ]
    time_format = "%I:%M %p"
