from locations.storefinders.elfsight import ElfsightSpider


class EvergreenIESpider(ElfsightSpider):
    name = "evergreen_ie"
    item_attributes = {"brand": "Evergreen", "brand_wikidata": "Q118139610"}
    host = "core.service.elfsight.com"
    api_key = "d5995826-ddef-4f7d-8ee5-20eeafc6a233"
