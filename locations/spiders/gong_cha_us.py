from locations.storefinders.storepoint import StorepointSpider


class GongChaUSSpider(StorepointSpider):
    name = "gong_cha_us"
    item_attributes = {"brand": "Gong Cha", "brand_wikidata": "Q5581670"}
    key = "161d1d5abc0b7c"
