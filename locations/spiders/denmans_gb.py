from locations.storefinders.rexel import RexelSpider


class DenmansGBSpider(RexelSpider):
    name = "denmans_gb"
    item_attributes = {"brand": "Denmans", "brand_wikidata": "Q116508855"}
    base_url = "www.denmans.co.uk/den"
    search_lat = 51
    search_lon = -0
