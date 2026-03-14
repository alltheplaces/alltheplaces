from locations.storefinders.yith import YithSpider


class BrowArt23USSpider(YithSpider):
    name = "brow_art_23_us"
    item_attributes = {"brand": "Brow Art 23", "brand_wikidata": "Q115675881"}
    allowed_domains = ["browart23.com"]
    requires_proxy = True
