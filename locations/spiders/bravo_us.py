from locations.storefinders.yext import YextSpider


class BravoUSSpider(YextSpider):
    name = "bravo_us"
    item_attributes = {"brand": "Bravo", "brand_wikidata": "Q16985159"}
    api_key = "62850d78675a712e91b03d1d5868d470"
