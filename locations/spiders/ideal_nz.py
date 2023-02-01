from locations.storefinders.rexel import RexelSpider


class IdealNZSpider(RexelSpider):
    name = "ideal_nz"
    item_attributes = {"brand": "Ideal (New Zealand)", "brand_wikidata": "Q"}
    base_url = "www.ideal.co.nz/nzi"
    search_lat = -41
    search_lon = 174
