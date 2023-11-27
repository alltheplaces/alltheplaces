from locations.storefinders.rexel import RexelSpider


class RexelAUSpider(RexelSpider):
    name = "rexel_au"
    item_attributes = {"brand": "Rexel", "brand_wikidata": "Q962489"}
    base_url = "www.rexel.com.au/are"
    search_lat = -23.7
    search_lon = 132.08
