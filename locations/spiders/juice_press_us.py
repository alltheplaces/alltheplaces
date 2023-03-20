from locations.storefinders.storepoint import StorepointSpider


class JuicePressUSSpider(StorepointSpider):
    name = "juice_press_us"
    item_attributes = {"brand": "Juice Press", "brand_wikidata": "Q27150131"}
    key = "15d4897d596fbd"
