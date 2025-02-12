from locations.storefinders.rexel import RexelSpider


class RexelGBSpider(RexelSpider):
    name = "rexel_gb"
    item_attributes = {"brand": "Rexel", "brand_wikidata": "Q962489"}
    base_url = "www.rexel.co.uk/uki"
    search_lat = 51
    search_lon = -0
    drop_attributes = {"image"}
