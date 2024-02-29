from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LeaderBRSpider(WPStoreLocatorSpider):
    name = "leader_br"
    item_attributes = {
        "brand_wikidata": "Q10316732",
        "brand": "Leader",
    }
    allowed_domains = [
        "institucional.lojasleader.com.br",
    ]
    time_format = "%I:%M %p"
