from locations.storefinders.rexel import RexelSpider


class RexelDESpider(RexelSpider):
    name = "rexel_de"
    item_attributes = {"brand": "Rexel (Germany)", "brand_wikidata": "Q962489"}
    base_url = "www.rexel.de"
    search_lat = 50
    search_lon = 11
