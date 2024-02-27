from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class CharlesVoegeleSpider(AgileStoreLocatorSpider):
    name = "charles_voegele"
    item_attributes = {
        "brand_wikidata": "Q1066326",
        "brand": "Charles Vögele",
    }
    allowed_domains = [
        "charles-voegele.com",
    ]
